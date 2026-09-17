"""WES API composition root: FastAPI app wiring routers, CORS, and telemetry."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.telemetry import configure_logging, get_logger
from app.routers import ai, realtime_ws, workstreams

settings = get_settings()
configure_logging(settings.environment)
logger = get_logger(__name__)

app = FastAPI(
    title="WES API",
    description="Kaufman Rossin Workstream Engagement System — showcase backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workstreams.router)
app.include_router(ai.router)
app.include_router(realtime_ws.router)


@app.get("/healthz", tags=["ops"])
async def healthz() -> dict:
    """Liveness/readiness probe target for AKS."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("wes_api.startup", environment=settings.environment)
