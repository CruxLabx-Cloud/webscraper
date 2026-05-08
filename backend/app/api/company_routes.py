"""Company intelligence routes — search, brief, refresh, watchlist, triggers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbDep
from app.models import Company, CompanyTrigger, PeopleSignal, WatchlistEntry
from app.schemas.company import (
    CompanyBrief,
    CompanyMetricsOut,
    CompanyNewsOut,
    CompanyOut,
    CompanySearchRequest,
    CompanySearchSuggestion,
    CompanyTriggerOut,
    JobOut,
    LeadershipOut,
    PeopleSignalOut,
    WatchlistAddRequest,
    WatchlistEntryOut,
    WatchlistUpdateRequest,
)
from app.services.company_intelligence import CompanyIntelligenceService, slugify
from app.services.company_repo import (
    get_company_with_brief,
    get_or_create_company,
    refresh_company_intelligence,
)

router = APIRouter(prefix="/companies", tags=["companies"])
intel = CompanyIntelligenceService()


def _to_brief(
    company: Company,
    signals: list[PeopleSignal] | None = None,
    triggers: list[CompanyTrigger] | None = None,
    news: list[dict] | None = None,
    metrics: list[dict] | None = None,
) -> CompanyBrief:
    return CompanyBrief(
        company=CompanyOut.model_validate(company),
        leadership=[LeadershipOut.model_validate(l) for l in company.leadership],
        jobs=[JobOut.model_validate(j) for j in company.jobs],
        people_signals=[
            PeopleSignalOut.model_validate(s) for s in (signals or [])
        ],
        triggers=[CompanyTriggerOut.model_validate(t) for t in (triggers or [])],
        news=[CompanyNewsOut.model_validate(n) for n in (news or [])],
        metrics=[CompanyMetricsOut.model_validate(m) for m in (metrics or [])],
    )


@router.get("/suggest", response_model=list[CompanySearchSuggestion])
async def suggest(q: str, limit: int = 8, db: DbDep = None) -> list[CompanySearchSuggestion]:
    """Return company search suggestions.

    Uses the external intelligence provider first; if that fails, fall back to
    local DB matches so the UI still receives suggestions during demos or when
    Tavily is unavailable.
    """
    if not q.strip():
        return []
    try:
        candidates = intel.search_companies(q.strip(), limit=limit)
        return [
            CompanySearchSuggestion(
                name=c["name"], slug=c["slug"], description=c.get("description")
            )
            for c in candidates
        ]
    except Exception:
        # Fallback: query local DB for companies with matching name
        if db is None:
            raise HTTPException(status_code=502, detail="Search provider unavailable")
        stmt = select(Company).where(Company.name.ilike(f"%{q.strip()}%"))
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        return [
            CompanySearchSuggestion(name=r.name, slug=r.slug, description=r.description)
            for r in rows
        ]


@router.post("/search", response_model=CompanyBrief)
async def search_company(req: CompanySearchRequest, db: DbDep) -> CompanyBrief:
    if not req.location or not req.location.strip():
        raise HTTPException(
            status_code=400,
            detail="Location is required for company intelligence searches.",
        )
    company = await get_or_create_company(db, req.name)

    needs_refresh = req.refresh or company.last_refreshed_at is None
    if needs_refresh:
        try:
            await refresh_company_intelligence(
                db,
                company,
                platforms=req.job_platforms,
                intel=intel,
                location_filter=req.location,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502, detail=f"Intelligence pipeline failed: {exc}"
            ) from exc

    hydrated = await get_company_with_brief(db, company.id, location=req.location)
    if not hydrated:
        raise HTTPException(status_code=500, detail="Company hydration failed")
    company_obj, signals, triggers = hydrated
    return _to_brief(company_obj, signals, triggers)


@router.get("/{slug}", response_model=CompanyBrief)
async def get_company(
    slug: str,
    db: DbDep,
    location: str | None = Query(default=None),
    max_age_hours: int | None = Query(default=None, ge=1, le=24 * 90),
) -> CompanyBrief:
    company = await db.scalar(select(Company).where(Company.slug == slug))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    hydrated = await get_company_with_brief(
        db, company.id, location=location, max_age_hours=max_age_hours
    )
    if not hydrated:
        raise HTTPException(status_code=404, detail="Company not found")
    company_obj, signals, triggers = hydrated
    return _to_brief(company_obj, signals, triggers)


@router.post("/{slug}/refresh", response_model=CompanyBrief)
async def refresh_company(
    slug: str,
    db: DbDep,
    platforms: list[str] | None = None,
    location: str | None = Query(default=None),
) -> CompanyBrief:
    if not location or not location.strip():
        raise HTTPException(
            status_code=400,
            detail="Location is required to refresh company intelligence.",
        )
    company = await db.scalar(select(Company).where(Company.slug == slug))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    try:
        await refresh_company_intelligence(
            db,
            company,
            platforms=platforms or ["naukri", "linkedin", "indeed"],
            intel=intel,
            location_filter=location,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Refresh failed: {exc}") from exc

    hydrated = await get_company_with_brief(db, company.id, location=location)
    if not hydrated:
        raise HTTPException(status_code=500, detail="Hydration failed")
    company_obj, signals, triggers = hydrated
    return _to_brief(company_obj, signals, triggers)


@router.get("/{slug}/triggers", response_model=list[CompanyTriggerOut])
async def list_triggers(
    slug: str,
    db: DbDep,
    location: str | None = Query(default=None),
    max_age_hours: int = Query(default=24 * 7, ge=1, le=24 * 90),
    trigger_type: str | None = Query(default=None),
) -> list[CompanyTriggerOut]:
    """Return time-windowed triggers — used for the 'last 1h / 24h / 7d' view."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import or_, func as sqlfunc

    company = await db.scalar(select(Company).where(Company.slug == slug))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    stmt = (
        select(CompanyTrigger)
        .where(CompanyTrigger.company_id == company.id)
        .where(
            or_(
                CompanyTrigger.occurred_at >= cutoff,
                CompanyTrigger.discovered_at >= cutoff,
            )
        )
    )
    if location:
        loc = location.strip().lower()
        stmt = stmt.where(
            or_(
                sqlfunc.lower(CompanyTrigger.location).contains(loc),
                CompanyTrigger.location.is_(None),
            )
        )
    if trigger_type:
        stmt = stmt.where(CompanyTrigger.trigger_type == trigger_type)
    stmt = stmt.order_by(CompanyTrigger.discovered_at.desc()).limit(80)
    rows = (await db.execute(stmt)).scalars().all()
    return [CompanyTriggerOut.model_validate(t) for t in rows]


# --- Watchlist ---

watchlist_router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def _entry_out(entry: WatchlistEntry) -> WatchlistEntryOut:
    return WatchlistEntryOut(
        id=entry.id,
        company=CompanyOut.model_validate(entry.company),
        cadence=entry.cadence,  # type: ignore[arg-type]
        weekly_day=entry.weekly_day,
        last_digest_at=entry.last_digest_at,
    )


@watchlist_router.get("", response_model=list[WatchlistEntryOut])
async def list_watchlist(db: DbDep, user: CurrentUser) -> list[WatchlistEntryOut]:
    rows = (
        await db.execute(
            select(WatchlistEntry)
            .where(WatchlistEntry.user_id == user.id)
            .options(selectinload(WatchlistEntry.company))
            .order_by(WatchlistEntry.created_at.desc())
        )
    ).scalars().all()
    return [_entry_out(e) for e in rows]


@watchlist_router.post("", response_model=WatchlistEntryOut, status_code=201)
async def add_watchlist(
    req: WatchlistAddRequest, db: DbDep, user: CurrentUser
) -> WatchlistEntryOut:
    company = await db.get(Company, req.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    existing = await db.scalar(
        select(WatchlistEntry).where(
            WatchlistEntry.user_id == user.id,
            WatchlistEntry.company_id == req.company_id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already on watchlist")
    entry = WatchlistEntry(
        user_id=user.id,
        company_id=req.company_id,
        cadence=req.cadence,
        weekly_day=req.weekly_day,
    )
    db.add(entry)
    await db.commit()
    hydrated = await db.scalar(
        select(WatchlistEntry)
        .where(WatchlistEntry.id == entry.id)
        .options(selectinload(WatchlistEntry.company))
    )
    return _entry_out(hydrated)  # type: ignore[arg-type]


@watchlist_router.patch("/{entry_id}", response_model=WatchlistEntryOut)
async def update_watchlist(
    entry_id: int,
    req: WatchlistUpdateRequest,
    db: DbDep,
    user: CurrentUser,
) -> WatchlistEntryOut:
    entry = await db.scalar(
        select(WatchlistEntry)
        .where(WatchlistEntry.id == entry_id, WatchlistEntry.user_id == user.id)
        .options(selectinload(WatchlistEntry.company))
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.cadence = req.cadence
    entry.weekly_day = req.weekly_day
    await db.commit()
    return _entry_out(entry)


@watchlist_router.delete("/{entry_id}", status_code=200, response_class=Response)
async def delete_watchlist(
    entry_id: int, db: DbDep, user: CurrentUser
) -> Response:
    entry = await db.scalar(
        select(WatchlistEntry).where(
            WatchlistEntry.id == entry_id, WatchlistEntry.user_id == user.id
        )
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()
    return Response(status_code=204)


@watchlist_router.post("/digest/preview", status_code=200)
async def trigger_digest(db: DbDep, user: CurrentUser) -> dict:
    """Manually trigger a digest send for the current user (useful for demos)."""
    from app.services.digest_email import send_digest_for_user

    log_entry = await send_digest_for_user(db, user)
    return {
        "status": log_entry.status,
        "company_count": log_entry.company_count,
        "new_jobs": log_entry.new_jobs,
        "new_leaders": log_entry.new_leaders,
        "error": log_entry.error,
    }
