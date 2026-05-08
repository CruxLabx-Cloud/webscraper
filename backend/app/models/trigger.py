from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.company import Company


class CompanyTrigger(Base):
    """A timestamped 'something happened' event for a company.

    Each trigger has:
    - trigger_type: hiring | leadership_change | funding | linkedin_post | mention
    - occurred_at: when the underlying event actually happened (post date,
      hire date, funding announcement date) — used for the 'last 1h / 24h /
      7d' filters in the UI.
    - location: extracted from the trigger text when relevant (job location,
      office opening city). Enables strict per-city filtering.
    - importance: 0..1 — drives "high-priority" badge in UI.
    """

    __tablename__ = "company_triggers"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "fingerprint", name="uq_company_trigger_fp"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    trigger_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(400))
    snippet: Mapped[str | None] = mapped_column(Text, default=None)
    location: Mapped[str | None] = mapped_column(String(120), default=None, index=True)
    source_url: Mapped[str] = mapped_column(String(800))
    source_platform: Mapped[str] = mapped_column(String(40))
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    fingerprint: Mapped[str] = mapped_column(String(120), index=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship()
