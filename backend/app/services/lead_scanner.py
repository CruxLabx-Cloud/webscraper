"""Find prospect posts ('I need <service>...') across the open web.

Used by the 'Find Clients' feature: a service provider enters what they offer
(e.g. 'voice agents for customer support') and we surface real posts from
Reddit, Twitter/X, Indie Hackers, Stack Overflow, Quora, and Hacker News
asking for that exact thing.

Reddit is queried directly via its public JSON endpoint (no auth required) so
we get fresh, real-time results without burning Tavily quota. The other
platforms use Tavily site-targeted searches which are already paid for in this
project's setup.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import httpx

from app.services.tavily_client import TavilyService
from app.services.web_scraper import DEFAULT_HEADERS

log = logging.getLogger("citracker.leads")

# Phrases people use when actively shopping for a service — high-intent.
INTENT_PHRASES: list[str] = [
    "looking for",
    "anyone know",
    "anyone build",
    "need help with",
    "need a",
    "need someone",
    "recommend",
    "any recommendations",
    "hire",
    "hiring",
    "freelancer",
    "agency",
    "vendor",
    "consultant",
    "willing to pay",
    "budget",
    "we need",
    "i need",
    "we are looking",
    "we're looking",
    "open to",
    "rfp",
    "rfq",
    "quote",
]

NEGATIVE_PHRASES: list[str] = [
    "i can build",
    "i offer",
    "i provide",
    "we provide",
    "i sell",
    "selling",
    "we built",
    "we sell",
    "i help",
    "dm me if you need",
]

# Default subreddits where service-buyers and founders post.
DEFAULT_SUBREDDITS: list[str] = [
    "Entrepreneur",
    "smallbusiness",
    "SaaS",
    "startups",
    "Business_Ideas",
    "EntrepreneurRideAlong",
    "marketing",
    "sales",
    "forhire",
    "slavelabour",
    "DoneDirtCheap",
    "freelance",
    "indiebiz",
    "AskMarketing",
]


@dataclass
class LeadRecord:
    title: str
    snippet: str
    source_platform: str
    source_url: str
    author: str | None
    posted_at: datetime | None
    intent_score: float
    matched_keywords: list[str]
    contact_hint: str | None
    fingerprint: str


def _fingerprint(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:24]


def _score_intent(text: str, query_terms: Iterable[str]) -> tuple[float, list[str]]:
    blob = (text or "").lower()
    matched: list[str] = []
    score = 0.0
    for q in query_terms:
        q = q.lower().strip()
        if q and q in blob:
            score += 0.25
            matched.append(q)
    intent_hits = sum(1 for p in INTENT_PHRASES if p in blob)
    score += min(intent_hits * 0.15, 0.6)
    if any(p in blob for p in NEGATIVE_PHRASES):
        score -= 0.5
    return max(0.0, min(score, 1.0)), matched


def _looks_like_buying_intent(text: str) -> bool:
    blob = (text or "").lower()
    if any(p in blob for p in NEGATIVE_PHRASES):
        return False
    return any(p in blob for p in INTENT_PHRASES)


def _extract_contact_hint(text: str) -> str | None:
    """Try to pull a DM/email/profile hint out of post body."""
    if not text:
        return None
    m = re.search(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", text)
    if m:
        return m.group(0)
    if re.search(r"\b(dm|pm|message|reach out)\b", text, re.IGNORECASE):
        return "Send a direct message"
    return None


def _query_terms(query: str) -> list[str]:
    cleaned = re.sub(r"[^\w\s]", " ", query.lower())
    words = [w for w in cleaned.split() if len(w) > 2]
    # Also include the full phrase
    return list({query.lower().strip(), *words})


# ---------------- Reddit (direct public JSON) ----------------


async def _reddit_search(
    client: httpx.AsyncClient,
    query: str,
    subreddit: str | None = None,
    limit: int = 15,
    time_filter: str = "month",
) -> list[dict]:
    """Hit Reddit's public JSON search endpoint."""
    base = "https://www.reddit.com"
    if subreddit:
        url = f"{base}/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "1",
            "sort": "new",
            "t": time_filter,
            "limit": str(limit),
        }
    else:
        url = f"{base}/search.json"
        params = {"q": query, "sort": "new", "t": time_filter, "limit": str(limit)}
    try:
        resp = await client.get(url, params=params, timeout=4.0)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [c["data"] for c in data.get("data", {}).get("children", [])]
    except (httpx.HTTPError, ValueError, KeyError):
        return []


def _reddit_to_lead(post: dict, query: str, query_terms: list[str]) -> LeadRecord | None:
    title = (post.get("title") or "").strip()
    body = (post.get("selftext") or "")[:1000]
    blob = f"{title}\n{body}"
    if not _looks_like_buying_intent(blob):
        return None
    score, matched = _score_intent(blob, query_terms)
    if score < 0.25:
        return None
    permalink = post.get("permalink") or ""
    url = f"https://www.reddit.com{permalink}" if permalink else (post.get("url") or "")
    if not url:
        return None
    posted = post.get("created_utc")
    posted_at = (
        datetime.fromtimestamp(int(posted), tz=timezone.utc) if posted else None
    )
    return LeadRecord(
        title=title[:380],
        snippet=(body or title)[:600],
        source_platform="reddit",
        source_url=url,
        author=post.get("author"),
        posted_at=posted_at,
        intent_score=score,
        matched_keywords=matched,
        contact_hint=_extract_contact_hint(body) or "Comment / DM via Reddit",
        fingerprint=_fingerprint(url),
    )


# ---------------- Tavily site-targeted (Twitter, IH, SO, Quora, HN) ----------------


async def _tavily_site(
    tavily: TavilyService,
    query: str,
    domains: list[str],
    max_results: int = 6,
) -> list[dict]:
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(
                tavily.search,
                f"{query} looking for OR need OR recommend OR hiring",
                max_results,
                "basic",
                domains,
                None,
            ),
            timeout=4.5,
        )
    except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
        log.warning("tavily failed for %s: %s", domains, exc)
        return []
    return [{"url": r.url, "title": r.title, "content": r.content} for r in results]


def _tavily_to_lead(
    item: dict, platform: str, query_terms: list[str]
) -> LeadRecord | None:
    title = (item.get("title") or "").strip()
    body = (item.get("content") or "").strip()
    blob = f"{title}\n{body}"
    if not _looks_like_buying_intent(blob):
        return None
    score, matched = _score_intent(blob, query_terms)
    if score < 0.25:
        return None
    url = item.get("url") or ""
    if not url:
        return None
    return LeadRecord(
        title=title[:380],
        snippet=(body or title)[:600],
        source_platform=platform,
        source_url=url,
        author=None,
        posted_at=None,
        intent_score=score,
        matched_keywords=matched,
        contact_hint=_extract_contact_hint(body),
        fingerprint=_fingerprint(url),
    )


# ---------------- Top-level scanner ----------------


class LeadScanner:
    def __init__(self, tavily: TavilyService | None = None) -> None:
        self._tavily = tavily

    @property
    def tavily(self) -> TavilyService:
        if self._tavily is None:
            self._tavily = TavilyService()
        return self._tavily

    async def scan(
        self,
        query: str,
        subreddits: list[str] | None = None,
        platforms: list[str] | None = None,
        deadline_seconds: float = 9.0,
    ) -> list[LeadRecord]:
        """Concurrent fan-out across all sources, deduped + ranked."""
        terms = _query_terms(query)
        subs = subreddits or DEFAULT_SUBREDDITS[:6]
        plats = set(
            platforms
            or ["reddit", "twitter", "indiehackers", "stackoverflow", "quora", "hn"]
        )

        async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
            tasks: list[asyncio.Task] = []

            if "reddit" in plats:
                # site-wide search + a few high-intent subreddits in parallel
                tasks.append(
                    asyncio.create_task(_reddit_search(client, query, None, 20))
                )
                for sub in subs:
                    tasks.append(
                        asyncio.create_task(_reddit_search(client, query, sub, 10))
                    )

            tavily_jobs: list[tuple[str, list[str]]] = []
            if "twitter" in plats:
                tavily_jobs.append(
                    ("twitter", ["twitter.com", "x.com"])
                )
            if "indiehackers" in plats:
                tavily_jobs.append(("indiehackers", ["indiehackers.com"]))
            if "stackoverflow" in plats:
                tavily_jobs.append(
                    (
                        "stackoverflow",
                        [
                            "stackoverflow.com",
                            "softwareengineering.stackexchange.com",
                        ],
                    )
                )
            if "quora" in plats:
                tavily_jobs.append(("quora", ["quora.com"]))
            if "hn" in plats:
                tavily_jobs.append(("hn", ["news.ycombinator.com"]))

            tavily_tasks: list[asyncio.Task] = [
                asyncio.create_task(_tavily_site(self.tavily, query, dom, 6))
                for _, dom in tavily_jobs
            ]

            try:
                reddit_batches: list[list[dict]] = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=False),
                    timeout=deadline_seconds,
                )
            except asyncio.TimeoutError:
                reddit_batches = []
            try:
                tavily_batches: list[list[dict]] = await asyncio.wait_for(
                    asyncio.gather(*tavily_tasks, return_exceptions=False),
                    timeout=deadline_seconds,
                )
            except asyncio.TimeoutError:
                tavily_batches = []

        leads: dict[str, LeadRecord] = {}

        for batch in reddit_batches:
            for post in batch:
                rec = _reddit_to_lead(post, query, terms)
                if rec and rec.fingerprint not in leads:
                    leads[rec.fingerprint] = rec

        for (platform, _), items in zip(tavily_jobs, tavily_batches):
            for item in items:
                rec = _tavily_to_lead(item, platform, terms)
                if rec and rec.fingerprint not in leads:
                    leads[rec.fingerprint] = rec

        ranked = sorted(leads.values(), key=lambda r: r.intent_score, reverse=True)
        return ranked
