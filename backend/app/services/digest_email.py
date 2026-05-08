"""Email digest builder + SMTP sender.

If SMTP is not configured we log the rendered email instead of sending — so the
local dev experience works out of the box even without a mail server.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Sequence

import aiosmtplib
from jinja2 import Environment, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import (
    Company,
    DigestLog,
    JobPosting,
    LeadershipProfile,
    User,
    WatchlistEntry,
)

log = logging.getLogger("citracker.digest")

_jinja = Environment(autoescape=select_autoescape(["html", "xml"]))

HTML_TEMPLATE = _jinja.from_string(
    """
<!doctype html>
<html><body style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; color:#111; max-width:640px; margin:0 auto; padding:24px;">
  <h2 style="margin:0 0 4px 0;">Company Intelligence Digest</h2>
  <p style="color:#666; margin:0 0 24px 0;">{{ now.strftime('%B %d, %Y') }} • {{ user.email }}</p>

  {% for block in blocks %}
    <div style="border:1px solid #e5e7eb; border-radius:12px; padding:20px; margin-bottom:20px;">
      <h3 style="margin:0 0 4px 0;">{{ block.company.name }}</h3>
      {% if block.company.location %}<p style="margin:0 0 16px 0; color:#666; font-size:13px;">{{ block.company.location }}</p>{% endif %}

      <h4 style="margin:16px 0 8px 0; color:#374151;">Leadership ({{ block.leaders|length }} {{ 'new' if block.leaders else '' }})</h4>
      {% if block.leaders %}
        <ul style="padding-left:18px; margin:0;">
          {% for l in block.leaders %}
            <li>{{ l.title }}: <strong>{{ l.name }}</strong>
              {% if l.linkedin_url %} • <a href="{{ l.linkedin_url }}">LinkedIn</a>{% endif %}
            </li>
          {% endfor %}
        </ul>
      {% else %}
        <p style="color:#666; margin:0;">No leadership changes since last update.</p>
      {% endif %}

      <h4 style="margin:16px 0 8px 0; color:#374151;">New Job Postings ({{ block.jobs|length }})</h4>
      {% if block.jobs %}
        <ul style="padding-left:18px; margin:0;">
          {% for j in block.jobs %}
            <li>
              <a href="{{ j.source_url }}"><strong>{{ j.title }}</strong></a>
              {% if j.location %} — {{ j.location }}{% endif %}
              <span style="color:#666; font-size:12px;"> ({{ j.source_platform }}{% if j.posted_at %}, {{ j.posted_at.strftime('%b %d') }}{% endif %})</span>
            </li>
          {% endfor %}
        </ul>
      {% else %}
        <p style="color:#666; margin:0;">No new job postings since last update.</p>
      {% endif %}

      <p style="margin-top:16px;"><a href="{{ base_url }}/companies/{{ block.company.slug }}" style="color:#2563eb;">View Full Brief →</a></p>
    </div>
  {% endfor %}

  <p style="font-size:12px; color:#888; text-align:center; margin-top:24px;">
    You receive this digest because you track companies on Company Intelligence Tracker.
    <br><a href="{{ base_url }}/settings" style="color:#888;">Change cadence or unsubscribe</a>
  </p>
</body></html>
""".strip()
)

TEXT_TEMPLATE = _jinja.from_string(
    """
Company Intelligence Digest — {{ now.strftime('%B %d, %Y') }}
For: {{ user.email }}

{% for block in blocks %}
== {{ block.company.name }}{% if block.company.location %} ({{ block.company.location }}){% endif %} ==

LEADERSHIP ({{ block.leaders|length }}):
{% if block.leaders %}{% for l in block.leaders %}- {{ l.title }}: {{ l.name }}{% if l.linkedin_url %} | {{ l.linkedin_url }}{% endif %}
{% endfor %}{% else %}No leadership changes.
{% endif %}
HIRING ({{ block.jobs|length }} new):
{% if block.jobs %}{% for j in block.jobs %}- {{ j.title }}{% if j.location %} ({{ j.location }}){% endif %} — {{ j.source_platform }}{% if j.posted_at %}, {{ j.posted_at.strftime('%b %d') }}{% endif %}
  {{ j.source_url }}
{% endfor %}{% else %}No new postings.
{% endif %}
Full brief: {{ base_url }}/companies/{{ block.company.slug }}

{% endfor %}

Manage cadence: {{ base_url }}/settings
""".strip()
)


async def build_digest_for_user(
    db: AsyncSession, user: User
) -> tuple[list[dict], int, int]:
    """Returns (blocks, total_new_jobs, total_new_leaders)."""
    rows = (
        await db.execute(
            select(WatchlistEntry)
            .where(WatchlistEntry.user_id == user.id)
            .where(WatchlistEntry.cadence != "off")
            .options(selectinload(WatchlistEntry.company))
        )
    ).scalars().all()

    blocks: list[dict] = []
    total_jobs = 0
    total_leaders = 0
    now = datetime.now(timezone.utc)

    for entry in rows:
        since = entry.last_digest_at or (now - timedelta(days=14))
        new_jobs: Sequence[JobPosting] = (
            await db.execute(
                select(JobPosting)
                .where(JobPosting.company_id == entry.company_id)
                .where(JobPosting.discovered_at >= since)
                .order_by(JobPosting.discovered_at.desc())
                .limit(15)
            )
        ).scalars().all()
        new_leaders: Sequence[LeadershipProfile] = (
            await db.execute(
                select(LeadershipProfile)
                .where(LeadershipProfile.company_id == entry.company_id)
                .where(LeadershipProfile.discovered_at >= since)
                .order_by(LeadershipProfile.discovered_at.desc())
                .limit(10)
            )
        ).scalars().all()
        if not new_jobs and not new_leaders:
            continue
        blocks.append(
            {"company": entry.company, "jobs": list(new_jobs), "leaders": list(new_leaders)}
        )
        total_jobs += len(new_jobs)
        total_leaders += len(new_leaders)

    return blocks, total_jobs, total_leaders


def render_digest(user: User, blocks: list[dict]) -> tuple[str, str, str]:
    ctx = {
        "user": user,
        "blocks": blocks,
        "now": datetime.now(timezone.utc),
        "base_url": settings.app_base_url.rstrip("/"),
    }
    subject = (
        f"Intelligence digest: {len(blocks)} update"
        f"{'s' if len(blocks) != 1 else ''} from your watchlist"
    )
    return subject, HTML_TEMPLATE.render(**ctx), TEXT_TEMPLATE.render(**ctx)


async def send_email(to: str, subject: str, html: str, text: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    if not settings.smtp_host:
        log.info("SMTP not configured — would send email to %s: %s", to, subject)
        return

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_use_tls,
    )


async def send_digest_for_user(db: AsyncSession, user: User) -> DigestLog:
    blocks, new_jobs, new_leaders = await build_digest_for_user(db, user)
    if not blocks:
        entry_log = DigestLog(
            user_id=user.id,
            company_count=0,
            new_jobs=0,
            new_leaders=0,
            status="skipped",
        )
        db.add(entry_log)
        await db.commit()
        return entry_log

    subject, html, text = render_digest(user, blocks)
    try:
        await send_email(user.email, subject, html, text)
        status = "sent"
        err: str | None = None
    except Exception as exc:  # noqa: BLE001
        log.exception("digest send failed")
        status = "failed"
        err = str(exc)[:500]

    # Mark watchlist last_digest_at on success
    if status == "sent":
        now = datetime.now(timezone.utc)
        for block in blocks:
            company: Company = block["company"]
            row = await db.scalar(
                select(WatchlistEntry).where(
                    WatchlistEntry.user_id == user.id,
                    WatchlistEntry.company_id == company.id,
                )
            )
            if row:
                row.last_digest_at = now

    entry_log = DigestLog(
        user_id=user.id,
        company_count=len(blocks),
        new_jobs=new_jobs,
        new_leaders=new_leaders,
        status=status,
        error=err,
    )
    db.add(entry_log)
    await db.commit()
    return entry_log
