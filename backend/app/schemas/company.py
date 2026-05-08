from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    slug: str
    name: str
    website: str | None = None
    location: str | None = None
    description: str | None = None
    linkedin_url: str | None = None


class CompanyOut(CompanyBase):
    id: int
    last_refreshed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadershipOut(BaseModel):
    id: int
    name: str
    title: str
    linkedin_url: str | None = None
    source_url: str | None = None
    confidence: float
    discovered_at: datetime

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: int
    title: str
    location: str | None = None
    seniority: str | None = None
    role_type: str | None = None
    posted_at: datetime | None = None
    source_platform: str
    source_url: str
    summary: str | None = None
    discovered_at: datetime

    class Config:
        from_attributes = True


class PeopleSignalOut(BaseModel):
    id: int
    person_name: str | None = None
    person_title: str | None = None
    signal_type: str
    snippet: str
    source_url: str
    source_platform: str
    skills_mentioned: str | None = None
    linkedin_url: str | None = None
    discovered_at: datetime

    class Config:
        from_attributes = True


class CompanyTriggerOut(BaseModel):
    id: int
    trigger_type: str
    title: str
    snippet: str | None = None
    location: str | None = None
    source_url: str
    source_platform: str
    occurred_at: datetime | None = None
    importance: float
    discovered_at: datetime

    class Config:
        from_attributes = True


class CompanyNewsOut(BaseModel):
    title: str
    snippet: str
    source_url: str
    source_platform: str
    news_type: str  # announcement | funding | acquisition | product_launch | partnership
    published_at: datetime | None = None

    class Config:
        from_attributes = True


class CompanyMetricsOut(BaseModel):
    metric_type: str  # employee_count | funding_stage | growth_signal | market_indicator
    value: str | int | None = None
    context: str | None = None
    source_url: str | None = None

    class Config:
        from_attributes = True


class CompanyBrief(BaseModel):
    company: CompanyOut
    leadership: list[LeadershipOut]
    jobs: list[JobOut]
    people_signals: list[PeopleSignalOut] = Field(default_factory=list)
    triggers: list[CompanyTriggerOut] = Field(default_factory=list)
    news: list[CompanyNewsOut] = Field(default_factory=list)
    metrics: list[CompanyMetricsOut] = Field(default_factory=list)


class CompanySearchRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    refresh: bool = False
    location: str | None = Field(
        default=None,
        max_length=120,
        description="Restrict jobs/triggers to this city (e.g. 'Chennai').",
    )
    job_platforms: list[
        Literal["naukri", "linkedin", "indeed", "foundit", "workindia"]
    ] = Field(default_factory=lambda: ["naukri", "linkedin", "indeed"])


class CompanySearchSuggestion(BaseModel):
    name: str
    slug: str
    description: str | None = None


class WatchlistEntryOut(BaseModel):
    id: int
    company: CompanyOut
    cadence: Literal["off", "biweekly", "weekly"]
    weekly_day: int
    last_digest_at: datetime | None = None

    class Config:
        from_attributes = True


class WatchlistAddRequest(BaseModel):
    company_id: int
    cadence: Literal["off", "biweekly", "weekly"] = "weekly"
    weekly_day: int = Field(default=0, ge=0, le=6)


class WatchlistUpdateRequest(BaseModel):
    cadence: Literal["off", "biweekly", "weekly"]
    weekly_day: int = Field(default=0, ge=0, le=6)
