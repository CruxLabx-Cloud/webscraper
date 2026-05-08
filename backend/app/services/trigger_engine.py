"""Detect time-stamped triggers for a company.

A trigger is anything that signals "this company just did something" —
hired a senior person, raised funding, opened a new office, posted on
LinkedIn, etc. We parse Tavily snippets for explicit dates / "X days ago"
markers and only persist triggers we can timestamp.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.services.tavily_client import TavilyService
from app.services.web_scraper import relative_to_datetime

log = logging.getLogger("citracker.triggers")

# Indian metro list — used to extract location from any snippet.
INDIAN_CITIES = [
    "bangalore", "bengaluru", "mumbai", "chennai", "hyderabad",
    "pune", "delhi", "new delhi", "noida", "gurgaon", "gurugram",
    "kolkata", "kochi", "ahmedabad", "jaipur", "indore", "trivandrum",
    "coimbatore", "visakhapatnam", "lucknow", "chandigarh", "nagpur",
    "thiruvananthapuram", "bhubaneswar", "madurai", "vadodara",
]
GLOBAL_HUBS = [
    "san francisco", "new york", "london", "singapore", "dubai",
    "berlin", "amsterdam", "tokyo", "sydney", "toronto", "remote", "hybrid",
]
LOCATION_PATTERNS = sorted(INDIAN_CITIES + GLOBAL_HUBS, key=len, reverse=True)
_LOC_RE = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in LOCATION_PATTERNS) + r")\b",
    re.IGNORECASE,
)

FUNDING_RE = re.compile(
    r"\b(raises?|raised|series\s+[a-f]|seed\s+round|funding|funded|"
    r"investment|valuation)\b",
    re.IGNORECASE,
)
LEADERSHIP_RE = re.compile(
    r"\b(appoint|appointed|joins as|new (ceo|cto|cfo|coo|chro|cmo|cpo|"
    r"vp|head)|hires?|promoted)\b",
    re.IGNORECASE,
)
HIRING_RE = re.compile(
    r"\b(hiring|now hiring|we'?re hiring|open roles?|join us|"
    r"job opening|position available|apply now)\b",
    re.IGNORECASE,
)


@dataclass
class TriggerRecord:
    trigger_type: str  # hiring | leadership_change | funding | linkedin_post | mention
    title: str
    snippet: str | None
    location: str | None
    source_url: str
    source_platform: str
    occurred_at: datetime | None
    importance: float
    fingerprint: str


def extract_location(text: str) -> str | None:
    if not text:
        return None
    m = _LOC_RE.search(text)
    if not m:
        return None
    raw = m.group(1).lower()
    # Normalize Indian aliases
    aliases = {
        "bangalore": "Bengaluru",
        "gurgaon": "Gurugram",
        "new delhi": "Delhi",
        "thiruvananthapuram": "Trivandrum",
    }
    return aliases.get(raw, raw.title())


def _classify(title: str, snippet: str) -> tuple[str, float]:
    blob = f"{title} {snippet}".lower()
    if FUNDING_RE.search(blob):
        return "funding", 0.95
    if LEADERSHIP_RE.search(blob):
        return "leadership_change", 0.85
    if HIRING_RE.search(blob):
        return "hiring", 0.7
    return "mention", 0.4


def _fp(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _detect_platform(url: str) -> str:
    if "linkedin.com" in url:
        return "linkedin"
    if "twitter.com" in url or "x.com" in url:
        return "twitter"
    if "crunchbase.com" in url:
        return "crunchbase"
    if "reddit.com" in url:
        return "reddit"
    return "web"


class TriggerEngine:
    def __init__(self, tavily: TavilyService | None = None) -> None:
        self._tavily = tavily

    @property
    def tavily(self) -> TavilyService:
        if self._tavily is None:
            self._tavily = TavilyService()
        return self._tavily

    async def _search(self, query: str, max_results: int = 6) -> list:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self.tavily.search, query, max_results, "basic", None, None
                ),
                timeout=4.0,
            )
        except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
            log.warning("trigger search failed: %s", exc)
            return []

    async def scan(
        self,
        company_name: str,
        location_filter: str | None = None,
        max_age_days: int = 30,
        deadline_seconds: float = 8.0,
    ) -> list[TriggerRecord]:
        """Run focused queries for each trigger type concurrently."""
        queries = [
            (f'"{company_name}" hiring OR "we are hiring" OR "join our team"', "hiring"),
            (f'"{company_name}" appointed OR "joins as" OR "new CEO" OR "new CTO"', "leadership_change"),
            (f'"{company_name}" raises OR funding OR "Series A" OR "Series B" OR investment', "funding"),
            (f'"{company_name}" announcement OR launch OR partnership site:linkedin.com', "linkedin_post"),
            (f'"{company_name}" news OR mention site:twitter.com OR site:x.com', "mention"),
        ]

        async def run(query: str, hint: str) -> list[TriggerRecord]:
            results = await self._search(query, max_results=5)
            out: list[TriggerRecord] = []
            for r in results:
                title = (r.title or "").strip()[:380]
                snippet = (r.content or "").strip()[:600]
                if not title and not snippet:
                    continue
                ttype, importance = _classify(title, snippet)
                # If the search was specifically for a type, prefer that label
                if ttype == "mention" and hint != "mention":
                    ttype, importance = hint, max(importance, 0.6)
                location = extract_location(f"{title} {snippet}")
                occurred = relative_to_datetime(snippet) or relative_to_datetime(title)
                out.append(
                    TriggerRecord(
                        trigger_type=ttype,
                        title=title,
                        snippet=snippet or None,
                        location=location,
                        source_url=r.url,
                        source_platform=_detect_platform(r.url),
                        occurred_at=occurred,
                        importance=importance,
                        fingerprint=_fp(r.url, ttype),
                    )
                )
            return out

        try:
            batches = await asyncio.wait_for(
                asyncio.gather(*(run(q, t) for q, t in queries)),
                timeout=deadline_seconds,
            )
        except asyncio.TimeoutError:
            batches = []

        merged: dict[str, TriggerRecord] = {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        loc_filter_norm = (location_filter or "").strip().lower() or None

        for batch in batches:
            for rec in batch:
                if rec.occurred_at and rec.occurred_at < cutoff:
                    continue
                if loc_filter_norm:
                    if not rec.location or loc_filter_norm not in rec.location.lower():
                        # Allow remote/hybrid through if location filter is set
                        if not rec.location or rec.location.lower() not in {"remote", "hybrid"}:
                            continue
                if rec.fingerprint not in merged:
                    merged[rec.fingerprint] = rec

        return sorted(
            merged.values(),
            key=lambda r: (
                r.occurred_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
                r.importance,
            ),
            reverse=True,
        )
