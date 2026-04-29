"""Orchestrator: composes Tavily search + Firecrawl scraping into one pipeline."""
from __future__ import annotations

from typing import Any

from app.schemas.jobs import (
    ScrapeResponse,
    SearchAndScrapeResponse,
    SearchResultItem,
)
from app.services.firecrawl_client import FirecrawlService
from app.services.tavily_client import TavilyService


class Orchestrator:
    def __init__(
        self,
        tavily: TavilyService | None = None,
        firecrawl: FirecrawlService | None = None,
    ) -> None:
        self._tavily = tavily
        self._firecrawl = firecrawl

    @property
    def tavily(self) -> TavilyService:
        if self._tavily is None:
            self._tavily = TavilyService()
        return self._tavily

    @property
    def firecrawl(self) -> FirecrawlService:
        if self._firecrawl is None:
            self._firecrawl = FirecrawlService()
        return self._firecrawl

    async def scrape_urls(
        self,
        urls: list[str],
        formats: list[str],
        only_main_content: bool = True,
        extraction_schema: dict[str, Any] | None = None,
        extraction_prompt: str | None = None,
    ) -> ScrapeResponse:
        results = await self.firecrawl.scrape_many(
            urls=urls,
            formats=formats,
            only_main_content=only_main_content,
            extraction_schema=extraction_schema,
            extraction_prompt=extraction_prompt,
        )
        succeeded = sum(1 for r in results if r.success)
        return ScrapeResponse(
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )

    async def search_and_scrape(
        self,
        query: str,
        max_results: int,
        formats: list[str],
        extraction_schema: dict[str, Any] | None = None,
        extraction_prompt: str | None = None,
    ) -> SearchAndScrapeResponse:
        sources: list[SearchResultItem] = self.tavily.search(
            query=query, max_results=max_results
        )
        urls = [s.url for s in sources]
        scraped = await self.scrape_urls(
            urls=urls,
            formats=formats,
            extraction_schema=extraction_schema,
            extraction_prompt=extraction_prompt,
        )
        return SearchAndScrapeResponse(
            query=query,
            sources=sources,
            scraped=scraped,
        )
