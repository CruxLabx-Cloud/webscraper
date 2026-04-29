"""Tavily search client wrapper.

Tavily handles the discovery phase: given a natural-language query, it returns
a ranked list of relevant URLs that we can then feed into Firecrawl.
"""
from __future__ import annotations

from typing import Any

from tavily import TavilyClient

from app.core.config import settings
from app.schemas.jobs import SearchResultItem


class TavilyService:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.tavily_api_key
        if not key:
            raise RuntimeError(
                "TAVILY_API_KEY is not configured. Add it to backend/.env"
            )
        self._client = TavilyClient(api_key=key)

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic",
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> list[SearchResultItem]:
        kwargs: dict[str, Any] = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains

        raw = self._client.search(**kwargs)
        items = raw.get("results", []) if isinstance(raw, dict) else []
        return [
            SearchResultItem(
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                score=item.get("score"),
            )
            for item in items
            if item.get("url")
        ]
