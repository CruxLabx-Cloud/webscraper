"""Lightweight, fast HTML scraper.

Used as a fallback / parallel path to Firecrawl: pulls page text via httpx +
BeautifulSoup with aggressive timeouts so we can complete a multi-source
intelligence scan in <10 seconds.

Browser-like User-Agent + accept-language headers reduce 403s on most public
job/profile pages without needing a headless browser.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class FetchedPage:
    url: str
    status: int
    title: str
    text: str
    meta_description: str | None
    fetched_at: datetime


_DATE_HINTS = re.compile(
    r"(\d+)\s*(hour|day|week|month|year)s?\s*ago", re.IGNORECASE
)


def relative_to_datetime(snippet: str | None) -> datetime | None:
    """Convert phrases like '3 days ago' / '2 weeks ago' to absolute UTC."""
    if not snippet:
        return None
    m = _DATE_HINTS.search(snippet)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    delta_seconds = {
        "hour": 3600,
        "day": 86400,
        "week": 86400 * 7,
        "month": 86400 * 30,
        "year": 86400 * 365,
    }[unit]
    from datetime import timedelta

    return datetime.now(timezone.utc) - timedelta(seconds=n * delta_seconds)


async def fetch(
    client: httpx.AsyncClient, url: str, timeout: float = 5.0
) -> FetchedPage | None:
    try:
        resp = await client.get(url, timeout=timeout, follow_redirects=True)
    except (httpx.HTTPError, asyncio.TimeoutError):
        return None
    if resp.status_code >= 400:
        return None
    try:
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception:  # noqa: BLE001
        soup = BeautifulSoup(resp.text, "html.parser")
    title = (soup.title.string if soup.title and soup.title.string else "").strip()
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    desc = (
        (desc_tag.get("content") if desc_tag else None) or ""
    ).strip() or None

    # Strip script/style and collapse whitespace.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:8000]
    return FetchedPage(
        url=url,
        status=resp.status_code,
        title=title,
        text=text,
        meta_description=desc,
        fetched_at=datetime.now(timezone.utc),
    )


async def fetch_many(
    urls: list[str], concurrency: int = 8, timeout: float = 5.0
) -> list[FetchedPage]:
    """Fan out fetches with bounded concurrency. Failed fetches are skipped."""
    if not urls:
        return []
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
        async def one(u: str) -> FetchedPage | None:
            async with sem:
                return await fetch(client, u, timeout=timeout)

        results = await asyncio.gather(*(one(u) for u in urls))
    return [r for r in results if r is not None]
