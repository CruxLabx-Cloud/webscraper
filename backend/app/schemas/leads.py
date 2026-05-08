from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LeadOpportunityOut(BaseModel):
    id: int
    title: str
    snippet: str
    source_platform: str
    source_url: str
    author: str | None = None
    posted_at: datetime | None = None
    intent_score: float
    matched_keywords: str | None = None
    service_query: str
    contact_hint: str | None = None
    saved: bool
    contacted: bool
    discovered_at: datetime

    class Config:
        from_attributes = True


PlatformKey = Literal[
    "reddit", "twitter", "indiehackers", "stackoverflow", "quora", "hn"
]


class LeadScanRequest(BaseModel):
    """User describes the service they offer; we go find buyers asking for it."""

    service: str = Field(..., min_length=3, max_length=200)
    platforms: list[PlatformKey] = Field(
        default_factory=lambda: [
            "reddit",
            "twitter",
            "indiehackers",
            "stackoverflow",
            "quora",
            "hn",
        ]
    )
    subreddits: list[str] | None = None
    persist: bool = True


class LeadUpdateRequest(BaseModel):
    saved: bool | None = None
    contacted: bool | None = None
