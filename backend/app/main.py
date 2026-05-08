from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.company_routes import router as companies_router, watchlist_router
from app.api.leads_routes import router as leads_router
from app.api.routes import router
from app.core.config import settings
from app.db.session import init_db
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await init_db()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Company Intelligence Tracker API",
        description=(
            "Aggregates C-suite leadership, multi-platform job postings, and "
            "scheduled email digests for tracked companies. Powered by Tavily + "
            "Firecrawl."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    app.include_router(companies_router, prefix="/api")
    app.include_router(watchlist_router, prefix="/api")
    app.include_router(leads_router, prefix="/api")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return Response(status_code=204)

    return app


app = create_app()
