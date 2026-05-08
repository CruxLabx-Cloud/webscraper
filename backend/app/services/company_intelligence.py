"""Fast, parallel Company Intelligence pipeline.

Three independent tracks fan out concurrently against a per-call deadline so a
full brief returns inside ~10s:

1. Leadership — Tavily site:linkedin.com/in queries, parsed from search snippets.
2. Jobs — Tavily site-targeted searches across each platform, parsed from
   snippets (no per-URL Firecrawl call — that was the latency killer).
3. People signals (lead-gen) — Tavily queries surfacing recruiter / hiring-
   manager posts mentioning the company, plus skill-requirement mentions.

For all three, results come from Tavily's content snippet (which already
contains the relevant text). A lightweight httpx+BeautifulSoup fetch is used
as a best-effort enrichment with a hard timeout, never as a blocker.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.schemas.jobs import SearchResultItem
from app.services.tavily_client import TavilyService
from app.services.web_scraper import fetch_many, relative_to_datetime

log = logging.getLogger("citracker.intel")

JOB_PLATFORMS: dict[str, list[str]] = {
    "naukri": ["naukri.com"],
    "linkedin": ["linkedin.com"],
    "indeed": ["indeed.com", "indeed.co.in"],
    "foundit": ["foundit.in", "monsterindia.com"],
    "workindia": ["workindia.in"],
}

PlatformKey = Literal["naukri", "linkedin", "indeed", "foundit", "workindia"]

LEADERSHIP_TITLES = [
    "CEO",
    "Co-Founder",
    "CTO",
    "CFO",
    "COO",
    "CHRO",
    "VP Engineering",
    "Head of Talent",
]

# Common tech / commercial skills we surface from job snippets.
SKILL_PATTERNS = re.compile(
    r"\b(react|next\.?js|node\.?js|typescript|javascript|python|django|flask|"
    r"fastapi|java|spring|kotlin|swift|aws|azure|gcp|kubernetes|docker|"
    r"terraform|postgres|mysql|mongodb|redis|kafka|spark|hadoop|tableau|"
    r"power\s?bi|salesforce|hubspot|sap|figma|product manager|data scientist|"
    r"machine learning|llm|gen\s?ai|devops|sre|qa|frontend|backend|fullstack)\b",
    re.IGNORECASE,
)

# Hiring-intent regexes for people signals.
HIRING_INTENT = re.compile(
    r"\b(we'?re hiring|now hiring|join (our|the) team|open roles?|looking for|"
    r"hiring (a|an|for)|recruiting|talent partner|talent acquisition)\b",
    re.IGNORECASE,
)

NAME_TITLE_PATTERN = re.compile(
    r"^([A-Z][a-zA-Z\.\-']+(?:\s+[A-Z][a-zA-Z\.\-']+){0,3})\s*[\|\-–—,]\s*"
    r"([A-Za-z][\w\s&/\.\-,]{2,60})"
)

PAGE_TITLE_RE = re.compile(r"^page\s*\d+$", re.IGNORECASE)
GENERIC_TITLE_RE = re.compile(
    r"^(home|careers|jobs|openings|vacancies|apply|search results)$",
    re.IGNORECASE,
)


# ---------- record types ----------


@dataclass
class LeaderRecord:
    name: str
    title: str
    linkedin_url: str | None
    source_url: str | None
    confidence: float


@dataclass
class JobRecord:
    title: str
    location: str | None
    posted_at: datetime | None
    source_platform: str
    source_url: str
    seniority: str | None
    role_type: str | None
    summary: str | None
    fingerprint: str
    skills: list[str] = field(default_factory=list)


@dataclass
class CompanyNewsRecord:
    title: str
    snippet: str
    source_url: str
    source_platform: str
    news_type: str  # announcement | funding | acquisition | product_launch | partnership
    published_at: datetime | None
    fingerprint: str


@dataclass
class CompanyMetricsRecord:
    metric_type: str  # employee_count | funding_stage | growth_signal | market_indicator
    value: str | int | None
    context: str | None
    source_url: str | None
    fingerprint: str


@dataclass
class PeopleSignalRecord:
    person_name: str | None
    person_title: str | None
    signal_type: str  # hiring_post | requirement | mention
    snippet: str
    source_url: str
    source_platform: str
    skills: list[str]
    linkedin_url: str | None
    fingerprint: str


# ---------- helpers ----------


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "company"


def _fp(*parts: str) -> str:
    raw = "|".join(p.lower().strip() for p in parts if p)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def _job_fingerprint(title: str, location: str | None, posted_at: datetime | None) -> str:
    title_norm = re.sub(r"\s+", " ", (title or "").lower()).strip()
    loc_norm = re.sub(r"\s+", " ", (location or "").lower()).strip()
    bucket = ""
    if posted_at:
        bucket = str(posted_at.date().toordinal() // 3)
    return _fp(title_norm, loc_norm, bucket)


def _detect_platform(url: str) -> str:
    for key, domains in JOB_PLATFORMS.items():
        if any(d in url for d in domains):
            return key
    return "web"


def _extract_skills(text: str) -> list[str]:
    found = {m.group(0).lower() for m in SKILL_PATTERNS.finditer(text or "")}
    return sorted(found)[:8]


def _parse_linkedin_title(title: str) -> tuple[str, str | None]:
    """Pull (name, role) out of LinkedIn-style page titles.

    LinkedIn /in/ result titles tend to be 'Jane Doe - CTO at Acme | LinkedIn'.
    """
    cleaned = re.sub(r"\s*\|\s*LinkedIn.*$", "", title or "").strip()
    m = NAME_TITLE_PATTERN.match(cleaned)
    if not m:
        return cleaned, None
    return m.group(1).strip(), m.group(2).strip()


def _normalize_role(role_text: str) -> str:
    r = role_text.lower()
    if any(x in r for x in ("engineer", "developer", "sde", "swe", "devops", "data")):
        return "tech"
    if any(x in r for x in ("sales", "account", "bd", "growth")):
        return "sales"
    if any(x in r for x in ("operations", "ops", "supply")):
        return "operations"
    if any(x in r for x in ("hr", "talent", "recruit", "people")):
        return "hr"
    return "other"


def _clean_title(title: str | None) -> str | None:
    cleaned = re.sub(r"\s*\|\s*LinkedIn.*$", "", title or "").strip()
    cleaned = re.sub(r"\s*[\-–—]\s*LinkedIn.*$", "", cleaned).strip()
    cleaned = re.sub(r"^\s*\[?page\s*\d+\]?\s*[:\-–—]?\s*", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned:
        return None
    if PAGE_TITLE_RE.match(cleaned) or GENERIC_TITLE_RE.match(cleaned):
        return None
    return cleaned


def _is_job_title(title: str, content: str) -> bool:
    """Check if the content looks like an actual job posting vs landing page."""
    title_norm = (title or "").strip().lower()
    blob = (title + " " + content).lower()
    
    # Exclude obvious landing/aggregate pages
    landing_patterns = re.compile(
        r"\b(careers|jobs\s+page|careers\s+page|recruitment|hiring\s+page|openings|apply\s+now|search results|all\s+jobs|"
        r"view\s+(our\s+)?jobs|see\s+(all\s+)?vacancies|browse\s+jobs|job\s+board|posted\s+on|filters|your\s+skills)\b",
        re.IGNORECASE
    )
    
    # Reject obvious aggregate/listing style titles.
    if re.search(r"^\d+\s+.+\s+(jobs?|vacancies|openings)\b", title_norm):
        return False
    if re.search(r"\b\d+\s+(jobs?|vacancies|openings)\b", title_norm):
        return False
    if re.search(r"\b(jobs?|vacancies|openings)\s+(in|at|for)\b", title_norm):
        return False
    if re.search(r"^(careers?|recruitment|jobs?|hiring|vacancies|openings)\b", title_norm):
        return False
    if re.search(r"\b(careers?\s+and\s+employment|jobs?,?\s+employment)\b", title_norm):
        return False
    if landing_patterns.search(blob):
        return False
    
    # Must contain actual job title indicators (single specific role, not plural/aggregate)
    job_indicators = re.compile(
        r"\b(engineer|developer|designer|manager|analyst|scientist|coordinator|specialist|"
        r"consultant|architect|lead|director|manager|officer|associate|executive|operator|technician|"
        r"sales|marketing|product|finance|hr|human\s+resources|recruiter|talent)\b",
        re.IGNORECASE
    )
    
    # Require at least one role indicator and avoid very short generic titles.
    if len(title_norm) < 6:
        return False
    return bool(job_indicators.search(blob))


def _is_company_relevant(company_name: str, *parts: str) -> bool:
    blob = " ".join(p for p in parts if p).lower()
    company = company_name.lower().strip()
    if not blob or not company:
        return False
    if company in blob:
        return True
    tokens = [t for t in re.split(r"\W+", company) if len(t) >= 4]
    if not tokens:
        return False
    return sum(1 for token in tokens if token in blob) >= max(1, len(tokens) // 2)


# ---------- service ----------


class CompanyIntelligenceService:
    def __init__(self, tavily: TavilyService | None = None) -> None:
        self._tavily = tavily

    @property
    def tavily(self) -> TavilyService:
        if self._tavily is None:
            self._tavily = TavilyService()
        return self._tavily

    # ---------- discovery ----------

    def search_companies(self, query: str, limit: int = 8) -> list[dict[str, str]]:
        results = self.tavily.search(
            query=f"{query} company official website",
            max_results=max(limit, 5),
            search_depth="basic",
        )
        seen: set[str] = set()
        out: list[dict[str, str]] = []
        for r in results:
            name = (r.title or "").split("|")[0].split(" - ")[0].strip()
            if not name:
                continue
            slug = slugify(name)
            if slug in seen:
                continue
            seen.add(slug)
            out.append(
                {
                    "name": name,
                    "slug": slug,
                    "description": (r.content or "")[:200],
                    "website": r.url,
                }
            )
            if len(out) >= limit:
                break
        return out

    # ---------- internal: tavily wrapper with deadline ----------

    async def _search(
        self,
        query: str,
        max_results: int = 5,
        domains: list[str] | None = None,
    ) -> list[SearchResultItem]:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self.tavily.search, query, max_results, "basic", domains, None
                ),
                timeout=4.0,
            )
        except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
            log.warning("tavily search failed for %r: %s", query[:60], exc)
            return []

    # ---------- leadership ----------

    async def fetch_leadership(self, company_name: str) -> list[LeaderRecord]:
        async def per_role(title: str) -> list[LeaderRecord]:
            results = await self._search(
                query=f'"{company_name}" {title} site:linkedin.com/in',
                max_results=2,
                domains=["linkedin.com"],
            )
            leaders: list[LeaderRecord] = []
            for r in results:
                if "linkedin.com/in" not in r.url:
                    continue
                name, parsed_title = _parse_linkedin_title(r.title or "")
                leaders.append(
                    LeaderRecord(
                        name=name or "Unknown",
                        title=parsed_title or title,
                        linkedin_url=r.url,
                        source_url=r.url,
                        confidence=0.85 if parsed_title else 0.6,
                    )
                )
            return leaders

        all_results = await asyncio.gather(*(per_role(t) for t in LEADERSHIP_TITLES))
        merged: list[LeaderRecord] = []
        seen: set[tuple[str, str]] = set()
        for batch in all_results:
            for rec in batch:
                key = (rec.name.lower(), rec.title.lower())
                if key in seen or rec.name == "Unknown":
                    continue
                seen.add(key)
                merged.append(rec)
        return merged

    # ---------- jobs ----------

    async def fetch_jobs(
        self,
        company_name: str,
        platforms: list[str],
        per_platform: int = 5,
    ) -> list[JobRecord]:
        def build_query(platform: str, fallback: bool = False) -> str:
            if platform == "linkedin":
                if fallback:
                    return f'site:linkedin.com/jobs/view "{company_name}" hiring OR "{company_name}" "job"'
                return f'"{company_name}" "job description" OR "responsibilities" OR "qualifications"'
            if platform == "naukri":
                if fallback:
                    return f'site:naukri.com "{company_name}" "job" OR "vacancy"'
                return f'"{company_name}" position OR role OR opening site:naukri.com'
            if platform == "indeed":
                if fallback:
                    return f'site:indeed.com "{company_name}" "hiring" OR "job"'
                return f'"{company_name}" hiring engineer OR developer OR position site:indeed.com'
            if fallback:
                return f'"{company_name}" "job" OR "career opportunity"'
            return f'"{company_name}" job opening position'

        async def per_platform_search(platform: str) -> list[JobRecord]:
            domains = JOB_PLATFORMS.get(platform)
            if not domains:
                return []

            results = await self._search(
                query=build_query(platform, fallback=False),
                max_results=per_platform * 2,  # Get more to filter down
                domains=domains,
            )

            # If primary query is sparse, retry with a broader query.
            if len(results) < max(2, per_platform // 2):
                more = await self._search(
                    query=build_query(platform, fallback=True),
                    max_results=per_platform * 2,
                    domains=domains,
                )
                results.extend(more)

            jobs: list[JobRecord] = []
            for r in results:
                title = _clean_title((r.title or "").split("|")[0].split(" - ")[0])
                if not title:
                    continue
                
                snippet = r.content or ""
                
                # Check if this is actually a job posting, not a landing page
                if not _is_job_title(title, snippet):
                    continue
                
                if not _is_company_relevant(company_name, title, snippet):
                    continue
                
                # Try to pull location out of snippet
                loc_m = re.search(
                    r"\b(remote|hybrid|bangalore|bengaluru|mumbai|chennai|hyderabad|"
                    r"pune|delhi|noida|gurgaon|gurugram|kolkata|kochi|jaipur)\b",
                    snippet + " " + title,
                    re.IGNORECASE,
                )
                location = loc_m.group(0).title() if loc_m else None
                posted_at = relative_to_datetime(snippet)
                skills = _extract_skills(title + " " + snippet)
                role_type = _normalize_role(title)
                fp = _job_fingerprint(title, location, posted_at)
                jobs.append(
                    JobRecord(
                        title=title[:280],
                        location=location,
                        posted_at=posted_at,
                        source_platform=platform,
                        source_url=r.url,
                        seniority=None,
                        role_type=role_type,
                        summary=snippet[:280] or None,
                        fingerprint=fp,
                        skills=skills,
                    )
                )
            return jobs[:per_platform]  # Limit to requested per-platform count

        platform_results = await asyncio.gather(
            *(per_platform_search(p) for p in platforms)
        )
        merged: dict[str, JobRecord] = {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=120)
        for batch in platform_results:
            for rec in batch:
                if rec.posted_at and rec.posted_at < cutoff:
                    continue
                if rec.fingerprint not in merged:
                    merged[rec.fingerprint] = rec
        return list(merged.values())

    # ---------- people / lead-gen signals ----------

    async def fetch_people_signals(
        self, company_name: str
    ) -> list[PeopleSignalRecord]:
        queries = [
            # Hiring signals
            (
                f'"{company_name}" "we are hiring" OR "now hiring" OR "join our team"',
                "web",
                "hiring_post",
            ),
            (
                f'"{company_name}" hiring engineer OR developer OR "software engineer"',
                "web",
                "hiring_post",
            ),
            # Talent acquisition signals
            (
                f'"{company_name}" recruiter OR "talent acquisition" OR "head of talent"',
                "linkedin",
                "mention",
            ),
            # Team expansion / growth signals
            (
                f'"{company_name}" "expanding team" OR "growing team" OR "scaling" site:linkedin.com',
                "linkedin",
                "hiring_post",
            ),
            # Funding / investment signals
            (
                f'"{company_name}" funding OR "series funding" OR "raised" OR "investment"',
                "web",
                "requirement",
            ),
            # LinkedIn company updates
            (
                f'"{company_name}" "hiring for" OR "open positions" site:linkedin.com/company',
                "linkedin",
                "hiring_post",
            ),
            # New hires / team announcements
            (
                f'"{company_name}" "joined as" OR "joins team" OR "is now" site:linkedin.com/in',
                "linkedin",
                "mention",
            ),
            # Skills/requirements hiring signals
            (
                f'"{company_name}" "skills:" OR "qualifications:" OR "we need" engineers',
                "web",
                "requirement",
            ),
        ]

        async def run(query: str, platform: str, signal_type: str) -> list[PeopleSignalRecord]:
            results = await self._search(query=query, max_results=5)
            out: list[PeopleSignalRecord] = []
            for r in results:
                content = (r.content or "").strip()
                title = (r.title or "").strip()
                if not content and not title:
                    continue
                # Only keep snippets that show hiring intent or skills
                blob = f"{title} {content}"
                if signal_type in {"hiring_post", "requirement"} and not (
                    HIRING_INTENT.search(blob) or SKILL_PATTERNS.search(blob)
                ):
                    continue
                # Try to lift a person name from the LinkedIn title pattern
                person_name: str | None = None
                person_title: str | None = None
                if "linkedin.com/in" in r.url:
                    person_name, person_title = _parse_linkedin_title(title)
                fp = _fp(r.url, signal_type)
                out.append(
                    PeopleSignalRecord(
                        person_name=person_name,
                        person_title=person_title,
                        signal_type=signal_type,
                        snippet=(content or title)[:400],
                        source_url=r.url,
                        source_platform=platform,
                        skills=_extract_skills(blob),
                        linkedin_url=(
                            r.url if "linkedin.com/in" in r.url else None
                        ),
                        fingerprint=fp,
                    )
                )
            return out

        batches = await asyncio.gather(*(run(q, p, t) for q, p, t in queries))
        seen: set[str] = set()
        merged: list[PeopleSignalRecord] = []
        for batch in batches:
            for rec in batch:
                if rec.fingerprint in seen:
                    continue
                seen.add(rec.fingerprint)
                merged.append(rec)
        return merged

    # ---------- top-level: gather everything in parallel ----------

    async def fetch_news_and_updates(
        self, company_name: str
    ) -> list[CompanyNewsRecord]:
        """Fetch company news, announcements, funding, partnerships."""
        queries = [
            # Funding & investment news
            (
                f'"{company_name}" "funding round" OR "Series A" OR "Series B" OR "Series C" OR "raised" OR "investment"',
                "web",
                "funding",
            ),
            # Product launches & announcements
            (
                f'"{company_name}" "launches" OR "announced" OR "releases" OR "introduces" OR "announces"',
                "web",
                "product_launch",
            ),
            # Acquisitions & partnerships
            (
                f'"{company_name}" "acquires" OR "acquisition" OR "partners with" OR "partnership" OR "merger"',
                "web",
                "acquisition",
            ),
            # Press releases & announcements
            (
                f'"{company_name}" "press release" OR "news" site:prnewswire.com OR site:businesswire.com',
                "web",
                "announcement",
            ),
            # Company milestones
            (
                f'"{company_name}" "1 million" OR "10 million" OR "100 million" OR "unicorn" OR "IPO" OR "milestone"',
                "web",
                "announcement",
            ),
        ]

        async def run(query: str, platform: str, news_type: str) -> list[CompanyNewsRecord]:
            results = await self._search(query=query, max_results=6)
            out: list[CompanyNewsRecord] = []
            for r in results:
                title = (r.title or "").strip()
                content = (r.content or "").strip()
                if not title or not content:
                    continue
                if len(title) < 10 or len(content) < 20:
                    continue
                published_at = relative_to_datetime(content)
                fp = _fp(r.url, title, news_type)
                out.append(
                    CompanyNewsRecord(
                        title=title[:200],
                        snippet=content[:300],
                        source_url=r.url,
                        source_platform=platform,
                        news_type=news_type,
                        published_at=published_at,
                        fingerprint=fp,
                    )
                )
            return out

        batches = await asyncio.gather(*(run(q, p, t) for q, p, t in queries))
        seen: set[str] = set()
        merged: list[CompanyNewsRecord] = []
        for batch in batches:
            for rec in batch:
                if rec.fingerprint in seen:
                    continue
                seen.add(rec.fingerprint)
                merged.append(rec)
        return merged[:10]  # Top 10 news items

    async def fetch_company_metrics(
        self, company_name: str
    ) -> list[CompanyMetricsRecord]:
        """Fetch company size, growth, market indicators."""
        queries = [
            # Employee count / company size
            (
                f'"{company_name}" "employees" OR "employee count" OR "team size" OR "headcount" OR "workforce"',
                "employee_count",
            ),
            # Growth signals
            (
                f'"{company_name}" "growth" OR "expanding" OR "scaled" OR "rapid growth" OR "year-over-year"',
                "growth_signal",
            ),
            # Revenue & financials
            (
                f'"{company_name}" "revenue" OR "ARR" OR "valuation" OR "profitable" OR "income"',
                "market_indicator",
            ),
            # Market position
            (
                f'"{company_name}" "market leader" OR "top player" OR "industry leader" OR "category leader"',
                "market_indicator",
            ),
            # Customer growth
            (
                f'"{company_name}" "customers" OR "clients" OR "user growth" OR "adoption"',
                "growth_signal",
            ),
        ]

        async def run(query: str, metric_type: str) -> list[CompanyMetricsRecord]:
            results = await self._search(query=query, max_results=4)
            out: list[CompanyMetricsRecord] = []
            for r in results:
                content = (r.content or "").strip()
                title = (r.title or "").strip()
                if not content and not title:
                    continue
                blob = f"{title} {content}"
                # Extract potential metrics
                metrics = re.findall(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:K|M|B|million|billion|thousand)?", blob)
                if not metrics:
                    continue
                fp = _fp(r.url, metric_type)
                out.append(
                    CompanyMetricsRecord(
                        metric_type=metric_type,
                        value=metrics[0] if metrics else None,
                        context=(content or title)[:150],
                        source_url=r.url,
                        fingerprint=fp,
                    )
                )
            return out

        batches = await asyncio.gather(*(run(q, t) for q, t in queries))
        seen: set[str] = set()
        merged: list[CompanyMetricsRecord] = []
        for batch in batches:
            for rec in batch:
                if rec.fingerprint in seen:
                    continue
                seen.add(rec.fingerprint)
                merged.append(rec)
        return merged

    async def gather_all(
        self,
        company_name: str,
        platforms: list[str],
        deadline_seconds: float = 12.0,
    ) -> tuple[list[LeaderRecord], list[JobRecord], list[PeopleSignalRecord], list[CompanyNewsRecord], list[CompanyMetricsRecord]]:
        """Run leadership + jobs + signals + news + metrics concurrently with a hard deadline."""
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    self.fetch_leadership(company_name),
                    self.fetch_jobs(company_name, platforms),
                    self.fetch_people_signals(company_name),
                    self.fetch_news_and_updates(company_name),
                    self.fetch_company_metrics(company_name),
                    return_exceptions=True,
                ),
                timeout=deadline_seconds,
            )
        except asyncio.TimeoutError:
            log.warning("intelligence pipeline hit deadline for %s", company_name)
            return [], [], [], [], []

        leaders: list[LeaderRecord] = []
        jobs: list[JobRecord] = []
        signals: list[PeopleSignalRecord] = []
        news: list[CompanyNewsRecord] = []
        metrics: list[CompanyMetricsRecord] = []

        for idx, payload in enumerate(results):
            if isinstance(payload, Exception):
                log.warning("intel sub-task %s failed for %s: %s", idx, company_name, payload)
                continue
            if idx == 0:
                leaders = payload
            elif idx == 1:
                jobs = payload
            elif idx == 2:
                signals = payload
            elif idx == 3:
                news = payload
            elif idx == 4:
                metrics = payload
        return leaders, jobs, signals, news, metrics
