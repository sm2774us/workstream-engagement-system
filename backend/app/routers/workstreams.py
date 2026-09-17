"""WES Workstreams API: CRUD + AI-workflow triggers, Entra-ID protected."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.security import Principal, get_current_principal
from app.core.telemetry import get_logger
from app.models.workstream import Workstream, WorkstreamEvent, WorkstreamStatus
from app.services.eventing import get_publisher
from app.services.realtime import get_broadcaster
from app.services.rust_client import RustEngineClient

router = APIRouter(prefix="/api/v1/workstreams", tags=["workstreams"])
logger = get_logger(__name__)

_store: dict[str, Workstream] = {}


@router.get("", response_model=list[Workstream])
async def list_workstreams(principal: Principal = Depends(get_current_principal)) -> list[Workstream]:
    """List all Workstreams visible to the authenticated principal."""
    return list(_store.values())


@router.post("", response_model=Workstream, status_code=201)
async def create_workstream(
    title: str,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Workstream:
    """Create a Workstream, score it via the Rust engine, and fan out events.

    Business logic (creation, validation, authorization) stays in Python
    per the JD; the latency-sensitive risk score is delegated to the
    Rust/Tonic engine; the resulting mutation is published to Event
    Hubs/Kafka and broadcast to live clients over SignalR -- exercising
    every integration point in one call path.
    """
    rust_client = RustEngineClient(settings.rust_engine_grpc_target)
    score = await rust_client.score_workstream(title, WorkstreamStatus.DRAFT.value)

    workstream = Workstream(
        id=str(uuid.uuid4()), title=title, risk_score=score, assignee=principal.subject
    )
    _store[workstream.id] = workstream

    event = WorkstreamEvent(event_type="workstream.created", workstream=workstream, actor=principal.subject)
    await get_publisher(settings).publish(event)
    await get_broadcaster(settings).broadcast(event)

    logger.info("workstream.created", id=workstream.id, risk_score=score)
    return workstream


@router.patch("/{workstream_id}/status", response_model=Workstream)
async def update_status(
    workstream_id: str,
    status: WorkstreamStatus,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Workstream:
    """Transition a Workstream's status, re-scoring and re-broadcasting."""
    workstream = _store.get(workstream_id)
    if workstream is None:
        raise HTTPException(status_code=404, detail="Workstream not found")

    rust_client = RustEngineClient(settings.rust_engine_grpc_target)
    workstream.status = status
    workstream.risk_score = await rust_client.score_workstream(workstream.title, status.value)

    event = WorkstreamEvent(event_type="workstream.status_changed", workstream=workstream, actor=principal.subject)
    await get_publisher(settings).publish(event)
    await get_broadcaster(settings).broadcast(event)

    return workstream
