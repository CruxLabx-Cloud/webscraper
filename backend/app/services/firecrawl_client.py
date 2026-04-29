"""Firecrawl scraping client wrapper.

Firecrawl handles deep page extraction: rendering JS, converting HTML to clean
markdown, optionally extracting structured JSON via LLM-powered schemas.
"""
from __future__ import annotations

import asyncio
from typing import Any

from firecrawl import FirecrawlApp

from app.core.config import settings
from app.schemas.jobs import ScrapeResultItem


class FirecrawlService:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.firecrawl_api_key
        if not key:
            raise RuntimeError(
                "FIRECRAWL_API_KEY is not configured. Add it to backend/.env"
            )
        self._client = FirecrawlApp(api_key=key)

    def _build_params(
        self,
        formats: list[str],
        only_main_content: bool,
        extraction_schema: dict[str, Any] | None,
        extraction_prompt: str | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "formats": list(formats),
            "onlyMainContent": only_main_content,
        }
        if extraction_schema or extraction_prompt:
            if "extract" not in params["formats"]:
                params["formats"].append("extract")
            params["extract"] = {}
            if extraction_schema:
                params["extract"]["schema"] = extraction_schema
            if extraction_prompt:
                params["extract"]["prompt"] = extraction_prompt
        return params

    def scrape_one(
        self,
        url: str,
        formats: list[str],
        only_main_content: bool = True,
        extraction_schema: dict[str, Any] | None = None,
        extraction_prompt: str | None = None,
    ) -> ScrapeResultItem:
        params = self._build_params(
            formats, only_main_content, extraction_schema, extraction_prompt
        )
        try:
            raw = self._client.scrape_url(url, params=params)
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            return ScrapeResultItem(
                url=url,
                success=True,
                markdown=data.get("markdown"),
                html=data.get("html"),
                links=data.get("links"),
                metadata=data.get("metadata", {}) or {},
                extracted=data.get("extract") or data.get("llm_extraction"),
            )
        except Exception as e:  # noqa: BLE001 - we surface error string to user
            return ScrapeResultItem(
                url=url,
                success=False,
                error=str(e),
            )

    async def scrape_many(
        self,
        urls: list[str],
        formats: list[str],
        only_main_content: bool = True,
        extraction_schema: dict[str, Any] | None = None,
        extraction_prompt: str | None = None,
        concurrency: int = 5,
    ) -> list[ScrapeResultItem]:
        sem = asyncio.Semaphore(concurrency)

        async def run_one(u: str) -> ScrapeResultItem:
            async with sem:
                return await asyncio.to_thread(
                    self.scrape_one,
                    u,
                    formats,
                    only_main_content,
                    extraction_schema,
                    extraction_prompt,
                )

        return await asyncio.gather(*[run_one(u) for u in urls])
