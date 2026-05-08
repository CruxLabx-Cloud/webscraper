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


class PeopleSignal(Base):
    """A lead-gen signal tied to a person at a company.

    Captures things like:
    - "Jane Doe (TA Manager) is hiring 3 engineers" — recruiter announcements
    - "John CTO posted: looking for candidates with React + AWS"
    - Hiring manager LinkedIn posts mentioning specific job requirements

    These let sales/recruiter teams see WHO to reach out to, not just what's
    posted on a job board.
    """

    __tablename__ = "people_signals"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "fingerprint", name="uq_company_signal_fp"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    person_name: Mapped[str | None] = mapped_column(String(200), default=None)
    person_title: Mapped[str | None] = mapped_column(String(200), default=None)
    signal_type: Mapped[str] = mapped_column(String(40))  # hiring_post | requirement | mention | funding
    snippet: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(800))
    source_platform: Mapped[str] = mapped_column(String(40))
    skills_mentioned: Mapped[str | None] = mapped_column(String(400), default=None)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), default=None)
    fingerprint: Mapped[str] = mapped_column(String(120), index=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship()
