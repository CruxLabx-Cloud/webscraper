from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User

Cadence = Literal["off", "biweekly", "weekly"]


class WatchlistEntry(Base):
    """A user's tracked company plus their digest cadence preference."""

    __tablename__ = "watchlist_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    # off | biweekly (Mon/Wed/Fri) | weekly
    cadence: Mapped[str] = mapped_column(String(20), default="weekly")
    weekly_day: Mapped[int] = mapped_column(default=0)  # 0=Mon..6=Sun
    last_digest_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="watchlist")
    company: Mapped["Company"] = relationship()
