"""Persist intelligence-service output into the DB."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Company,
    CompanyTrigger,
    JobPosting,
    LeadershipProfile,
    PeopleSignal,
)
from app.services.company_intelligence import (
    CompanyIntelligenceService,
    JobRecord,
    LeaderRecord,
    PeopleSignalRecord,
    slugify,
)
from app.services.trigger_engine import TriggerEngine, TriggerRecord


async def get_or_create_company(
    db: AsyncSession, name: str, *, website: str | None = None
) -> Company:
    slug = slugify(name)
    company = await db.scalar(select(Company).where(Company.slug == slug))
    if company:
        return company
    company = Company(slug=slug, name=name.strip(), website=website)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def upsert_leadership(
    db: AsyncSession, company: Company, leaders: list[LeaderRecord]
) -> int:
    inserted = 0
    existing = {
        (l.name.lower(), l.title.lower())
        for l in (
            await db.execute(
                select(LeadershipProfile).where(
                    LeadershipProfile.company_id == company.id
                )
            )
        ).scalars()
    }
    for rec in leaders:
        key = (rec.name.lower(), rec.title.lower())
        if key in existing:
            continue
        db.add(
            LeadershipProfile(
                company_id=company.id,
                name=rec.name,
                title=rec.title,
                linkedin_url=rec.linkedin_url,
                source_url=rec.source_url,
                confidence=rec.confidence,
            )
        )
        existing.add(key)
        inserted += 1
    await db.commit()
    return inserted


async def upsert_jobs(
    db: AsyncSession, company: Company, jobs: list[JobRecord]
) -> int:
    inserted = 0
    existing_fps = {
        fp
        for fp in (
            await db.execute(
                select(JobPosting.fingerprint).where(
                    JobPosting.company_id == company.id
                )
            )
        ).scalars()
    }
    for rec in jobs:
        if rec.fingerprint in existing_fps:
            continue
        db.add(
            JobPosting(
                company_id=company.id,
                title=rec.title,
                location=rec.location,
                seniority=rec.seniority,
                role_type=rec.role_type,
                posted_at=rec.posted_at,
                source_platform=rec.source_platform,
                source_url=rec.source_url,
                fingerprint=rec.fingerprint,
                summary=rec.summary,
            )
        )
        existing_fps.add(rec.fingerprint)
        inserted += 1
    await db.commit()
    return inserted


async def upsert_people_signals(
    db: AsyncSession, company: Company, signals: list[PeopleSignalRecord]
) -> int:
    inserted = 0
    existing_fps = {
        fp
        for fp in (
            await db.execute(
                select(PeopleSignal.fingerprint).where(
                    PeopleSignal.company_id == company.id
                )
            )
        ).scalars()
    }
    for rec in signals:
        if rec.fingerprint in existing_fps:
            continue
        db.add(
            PeopleSignal(
                company_id=company.id,
                person_name=rec.person_name,
                person_title=rec.person_title,
                signal_type=rec.signal_type,
                snippet=rec.snippet,
                source_url=rec.source_url,
                source_platform=rec.source_platform,
                skills_mentioned=", ".join(rec.skills) if rec.skills else None,
                linkedin_url=rec.linkedin_url,
                fingerprint=rec.fingerprint,
            )
        )
        existing_fps.add(rec.fingerprint)
        inserted += 1
    await db.commit()
    return inserted


async def upsert_triggers(
    db: AsyncSession, company: Company, triggers: list[TriggerRecord]
) -> int:
    inserted = 0
    existing_fps = {
        fp
        for fp in (
            await db.execute(
                select(CompanyTrigger.fingerprint).where(
                    CompanyTrigger.company_id == company.id
                )
            )
        ).scalars()
    }
    for rec in triggers:
        if rec.fingerprint in existing_fps:
            continue
        db.add(
            CompanyTrigger(
                company_id=company.id,
                trigger_type=rec.trigger_type,
                title=rec.title,
                snippet=rec.snippet,
                location=rec.location,
                source_url=rec.source_url,
                source_platform=rec.source_platform,
                occurred_at=rec.occurred_at,
                importance=rec.importance,
                fingerprint=rec.fingerprint,
            )
        )
        existing_fps.add(rec.fingerprint)
        inserted += 1
    await db.commit()
    return inserted


async def refresh_company_intelligence(
    db: AsyncSession,
    company: Company,
    platforms: list[str],
    intel: CompanyIntelligenceService | None = None,
    location_filter: str | None = None,
) -> tuple[int, int, int, int]:
    """Hydrate leadership + jobs + people signals + triggers in parallel.

    Returns (new_leaders, new_jobs, new_signals, new_triggers).
    """
    import asyncio

    intel = intel or CompanyIntelligenceService()
    trig = TriggerEngine()

    intel_task = intel.gather_all(
        company.name, platforms=platforms, deadline_seconds=12.0
    )
    triggers_task = trig.scan(
        company.name, location_filter=location_filter, deadline_seconds=8.0
    )
    (leaders, jobs, signals, news, metrics), triggers = await asyncio.gather(
        intel_task, triggers_task
    )

    # If a location filter was given, drop jobs whose location doesn't match.
    if location_filter:
        loc = location_filter.strip().lower()
        jobs = [
            j for j in jobs
            if (not j.location)
            or (j.location and loc in j.location.lower())
            or (j.location and j.location.lower() in {"remote", "hybrid"})
        ]

    # Replace old jobs on refresh so improved filters purge stale junk rows.
    await db.execute(delete(JobPosting).where(JobPosting.company_id == company.id))
    await db.commit()

    new_leaders = await upsert_leadership(db, company, leaders)
    new_jobs = await upsert_jobs(db, company, jobs)
    new_signals = await upsert_people_signals(db, company, signals)
    new_triggers = await upsert_triggers(db, company, triggers)

    company.last_refreshed_at = datetime.now(timezone.utc)
    await db.commit()
    return new_leaders, new_jobs, new_signals, new_triggers


async def get_company_with_brief(
    db: AsyncSession,
    company_id: int,
    location: str | None = None,
    max_age_hours: int | None = None,
) -> tuple[Company, list[PeopleSignal], list[CompanyTrigger]] | None:
    """Eager-loads leadership + jobs (filtered) + people signals + triggers.

    Returns None if company not found.
    """
    from datetime import timedelta

    company = await db.scalar(
        select(Company)
        .where(Company.id == company_id)
        .options(
            selectinload(Company.leadership),
            selectinload(Company.jobs),
        )
    )
    if not company:
        return None

    if location:
        loc = location.strip().lower()
        company.jobs = [
            j for j in company.jobs
            if (not j.location)
            or (j.location and loc in j.location.lower())
            or (j.location and j.location.lower() in {"remote", "hybrid"})
        ]

    signals = (
        await db.execute(
            select(PeopleSignal)
            .where(PeopleSignal.company_id == company_id)
            .order_by(PeopleSignal.discovered_at.desc())
            .limit(40)
        )
    ).scalars().all()

    trig_stmt = select(CompanyTrigger).where(CompanyTrigger.company_id == company_id)
    if location:
        loc = location.strip().lower()
        from sqlalchemy import or_, func as sqlfunc
        trig_stmt = trig_stmt.where(
            or_(
                sqlfunc.lower(CompanyTrigger.location).contains(loc),
                CompanyTrigger.location.is_(None),
            )
        )
    if max_age_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        from sqlalchemy import or_
        trig_stmt = trig_stmt.where(
            or_(
                CompanyTrigger.occurred_at >= cutoff,
                CompanyTrigger.discovered_at >= cutoff,
            )
        )
    trig_stmt = trig_stmt.order_by(CompanyTrigger.discovered_at.desc()).limit(60)
    triggers = (await db.execute(trig_stmt)).scalars().all()

    return company, list(signals), list(triggers)
