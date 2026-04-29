from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse

from app.schemas.jobs import (
    ScrapeRequest,
    ScrapeResponse,
    SearchAndScrapeRequest,
    SearchAndScrapeResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.exporter import to_csv, to_json
from app.services.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    try:
        results = orchestrator.tavily.search(
            query=req.query,
            max_results=req.max_results,
            search_depth=req.search_depth,
            include_domains=req.include_domains or None,
            exclude_domains=req.exclude_domains or None,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Tavily error: {e}")
    return SearchResponse(query=req.query, results=results)


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(req: ScrapeRequest) -> ScrapeResponse:
    try:
        return await orchestrator.scrape_urls(
            urls=req.urls,
            formats=req.formats,
            only_main_content=req.only_main_content,
            extraction_schema=req.extraction_schema,
            extraction_prompt=req.extraction_prompt,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Firecrawl error: {e}")


@router.post("/search-and-scrape", response_model=SearchAndScrapeResponse)
async def search_and_scrape(req: SearchAndScrapeRequest) -> SearchAndScrapeResponse:
    try:
        return await orchestrator.search_and_scrape(
            query=req.query,
            max_results=req.max_results,
            formats=req.formats,
            extraction_schema=req.extraction_schema,
            extraction_prompt=req.extraction_prompt,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Pipeline error: {e}")


@router.post("/export")
async def export(
    payload: dict,
    fmt: str = Query("json", pattern="^(json|csv)$"),
) -> Response:
    """Convert a list of result rows into a downloadable JSON or CSV.

    Body shape: {"items": [ {...}, {...} ]}
    """
    items = payload.get("items")
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Body must include 'items' list")
    if fmt == "csv":
        body = to_csv(items)
        return PlainTextResponse(
            content=body,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="export.csv"'},
        )
    body = to_json(items)
    return PlainTextResponse(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="export.json"'},
    )
