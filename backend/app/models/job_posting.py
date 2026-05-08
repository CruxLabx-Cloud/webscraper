from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
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


class JobPosting(Base):
    """A single job listing aggregated for a company.

    The fingerprint column dedupes equivalent postings across platforms
    (title + location + 3-day date bucket).
    """

    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "fingerprint", name="uq_company_job_fingerprint"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    location: Mapped[str | None] = mapped_column(String(200), default=None)
    seniority: Mapped[str | None] = mapped_column(String(80), default=None)
    role_type: Mapped[str | None] = mapped_column(String(80), default=None)
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    source_platform: Mapped[str] = mapped_column(String(40))
    source_url: Mapped[str] = mapped_column(String(800))
    fingerprint: Mapped[str] = mapped_column(String(120), index=True)
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship(back_populates="jobs")
