from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    max_results: int = Field(10, ge=1, le=50)
    search_depth: Literal["basic", "advanced"] = "basic"
    include_domains: list[str] = Field(default_factory=list)
    exclude_domains: list[str] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    url: str
    title: str
    content: str
    score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]


class ScrapeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)
    formats: list[Literal["markdown", "html", "links"]] = Field(
        default_factory=lambda: ["markdown"]
    )
    only_main_content: bool = True
    extraction_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional JSON schema for structured extraction",
    )
    extraction_prompt: Optional[str] = Field(
        default=None,
        description="Optional natural-language extraction instruction",
    )


class ScrapeResultItem(BaseModel):
    url: str
    success: bool
    markdown: Optional[str] = None
    html: Optional[str] = None
    links: Optional[list[str]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    extracted: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class ScrapeResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[ScrapeResultItem]


class SearchAndScrapeRequest(BaseModel):
    query: str
    max_results: int = Field(5, ge=1, le=20)
    formats: list[Literal["markdown", "html", "links"]] = Field(
        default_factory=lambda: ["markdown"]
    )
    extraction_schema: Optional[dict[str, Any]] = None
    extraction_prompt: Optional[str] = None


class SearchAndScrapeResponse(BaseModel):
    query: str
    sources: list[SearchResultItem]
    scraped: ScrapeResponse
