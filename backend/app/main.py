"""Main FastAPI application entry point for PulseOps API."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.routes import auth, dashboard, endpoints, incidents, notifications, sse
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("pulseops.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle hooks."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' environment...")
    logger.info(f"Configured CORS origins: {settings.cors_origins_list}")
    try:
        from app.db.base import Base
        from app.db.session import engine
        from app.models import (  # noqa: F401
            check,
            endpoint,
            incident,
            incident_event,
            notification,
            user,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized and verified.")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Database schema auto-sync note: {e}")

    worker_task = None
    if settings.START_EMBEDDED_WORKER:
        from app.workers.scheduler import start_worker_loop

        worker_task = asyncio.create_task(start_worker_loop())
        logger.info("Embedded monitoring worker started.")

    yield

    if worker_task:
        worker_task.cancel()
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title="PulseOps API",
    description="Real-time API Monitoring, Latency Analytics & Incident Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


# Include versioned API routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(endpoints.router, prefix=settings.API_PREFIX)
app.include_router(incidents.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(sse.router, prefix=settings.API_PREFIX)

# Static Frontend SPA serving for unified deployment
dist_candidates = [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent.parent / "frontend" / "dist",
    Path("/app/frontend/dist"),
]
dist_dir: Path | None = None
for candidate in dist_candidates:
    if candidate.exists() and (candidate / "index.html").exists():
        dist_dir = candidate
        break

if settings.SERVE_FRONTEND and dist_dir:
    logger.info(f"Serving frontend SPA from: {dist_dir}")
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if (
            full_path.startswith(("api", "docs", "redoc"))
            or full_path == "health"
        ):
            raise HTTPException(status_code=404)
        target = dist_dir / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(dist_dir / "index.html")
else:

    @app.get("/", tags=["System"], include_in_schema=False)
    async def root():
        return {
            "message": "Welcome to PulseOps API Monitoring Platform",
            "docs": "/docs",
            "health": "/health",
        }

