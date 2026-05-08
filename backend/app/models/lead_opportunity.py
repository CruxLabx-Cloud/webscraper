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
    from app.models.user import User


class LeadOpportunity(Base):
    """A real-world post from someone *requesting* a service / product.

    Example: a Reddit thread "Looking for someone to build a voice agent for
    our SaaS support" — that's a buying signal for any team that builds
    voice agents. We scrape such posts across Reddit, Twitter/X, Indie
    Hackers, Stack Overflow, Quora, and Hacker News so the user (a service
    provider) can reach out cold with high relevance.

    Owned by a user so each user gets their own scoped lead inbox.
    """

    __tablename__ = "lead_opportunities"
    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint", name="uq_user_lead_fp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(400))
    snippet: Mapped[str] = mapped_column(Text)
    source_platform: Mapped[str] = mapped_column(String(40), index=True)
    source_url: Mapped[str] = mapped_column(String(800))
    author: Mapped[str | None] = mapped_column(String(200), default=None)
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    intent_score: Mapped[float] = mapped_column(Float, default=0.5)
    matched_keywords: Mapped[str | None] = mapped_column(String(500), default=None)
    service_query: Mapped[str] = mapped_column(String(200), index=True)
    contact_hint: Mapped[str | None] = mapped_column(String(400), default=None)
    fingerprint: Mapped[str] = mapped_column(String(120), index=True)
    saved: Mapped[bool] = mapped_column(default=False, index=True)
    contacted: Mapped[bool] = mapped_column(default=False, index=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship()
