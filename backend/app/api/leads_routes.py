"""Lead Opportunity routes — find prospects asking for the user's service."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from app.api.deps import DbDep
from app.models import LeadOpportunity
from app.schemas.leads import LeadOpportunityOut, LeadScanRequest, LeadUpdateRequest
from app.services.lead_scanner import LeadScanner

router = APIRouter(prefix="/leads", tags=["leads"])
scanner = LeadScanner()


@router.post("/scan", response_model=list[LeadOpportunityOut])
async def scan_leads(req: LeadScanRequest, db: DbDep) -> list[LeadOpportunityOut]:
    try:
        records = await scanner.scan(
            query=req.service,
            subreddits=req.subreddits,
            platforms=list(req.platforms),
            deadline_seconds=9.0,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Lead scan failed: {exc}") from exc

    if not req.persist:
        return [
            LeadOpportunityOut(
                id=0,
                title=r.title,
                snippet=r.snippet,
                source_platform=r.source_platform,
                source_url=r.source_url,
                author=r.author,
                posted_at=r.posted_at,
                intent_score=r.intent_score,
                matched_keywords=", ".join(r.matched_keywords) or None,
                service_query=req.service,
                contact_hint=r.contact_hint,
                saved=False,
                contacted=False,
                discovered_at=r.posted_at or __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
            )
            for r in records
        ]

    # Without auth, just return the ephemeral records
    return [
        LeadOpportunityOut(
            id=idx + 1,
            title=r.title,
            snippet=r.snippet,
            source_platform=r.source_platform,
            source_url=r.source_url,
            author=r.author,
            posted_at=r.posted_at,
            intent_score=r.intent_score,
            matched_keywords=", ".join(r.matched_keywords) or None,
            service_query=req.service,
            contact_hint=r.contact_hint,
            saved=False,
            contacted=False,
            discovered_at=r.posted_at or __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        )
        for idx, r in enumerate(records)
    ]


@router.get("", response_model=list[LeadOpportunityOut])
async def list_leads(db: DbDep) -> list[LeadOpportunityOut]:
    return []


@router.get("/services", response_model=list[str])
async def list_service_queries(db: DbDep) -> list[str]:
    return []