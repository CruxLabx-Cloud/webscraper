"""APScheduler glue for digest delivery.

Runs an in-process AsyncIOScheduler that fires once an hour and decides which
users are due a digest based on their watchlist cadence:

- biweekly: Mon/Wed/Fri at 09:00 UTC
- weekly: chosen weekday at 09:00 UTC (per WatchlistEntry.weekly_day)

We dedupe per-user per-day so a user with both biweekly and weekly entries only
gets one consolidated digest per day.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import User, WatchlistEntry
from app.services.digest_email import send_digest_for_user

log = logging.getLogger("citracker.scheduler")

_scheduler: AsyncIOScheduler | None = None

BIWEEKLY_DAYS = {0, 2, 4}  # Mon, Wed, Fri
DIGEST_HOUR_UTC = 9


async def run_due_digests() -> None:
    now = datetime.now(timezone.utc)
    if now.hour != DIGEST_HOUR_UTC:
        return

    weekday = now.weekday()
    async with SessionLocal() as db:
        # Find user IDs with any due watchlist entry today
        biweekly_due = weekday in BIWEEKLY_DAYS
        clauses = []
        if biweekly_due:
            clauses.append(WatchlistEntry.cadence == "biweekly")
        clauses.append(
            (WatchlistEntry.cadence == "weekly")
            & (WatchlistEntry.weekly_day == weekday)
        )

        from sqlalchemy import or_

        rows = (
            await db.execute(
                select(WatchlistEntry.user_id).where(or_(*clauses)).distinct()
            )
        ).scalars().all()

        for user_id in rows:
            user = await db.get(User, user_id)
            if not user:
                continue
            try:
                result = await send_digest_for_user(db, user)
                log.info(
                    "digest user=%s status=%s jobs=%s leaders=%s",
                    user.email,
                    result.status,
                    result.new_jobs,
                    result.new_leaders,
                )
            except Exception:  # noqa: BLE001
                log.exception("digest failed for user_id=%s", user_id)


def start_scheduler() -> None:
    global _scheduler
    if not settings.scheduler_enabled:
        log.info("scheduler disabled by config")
        return
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    # Fire every hour at minute 5; the job filters to the configured digest hour.
    _scheduler.add_job(run_due_digests, "cron", minute=5, id="digest_dispatcher")
    _scheduler.start()
    log.info("scheduler started (digests at %02d:05 UTC)", DIGEST_HOUR_UTC)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
