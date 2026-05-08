from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.company import Company


class LeadershipProfile(Base):
    __tablename__ = "leadership_profiles"
    __table_args__ = (
        UniqueConstraint("company_id", "name", "title", name="uq_company_role_person"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    linkedin_url: Mapped[str | None] = mapped_column(String(500), default=None)
    source_url: Mapped[str | None] = mapped_column(String(500), default=None)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship(back_populates="leadership")
