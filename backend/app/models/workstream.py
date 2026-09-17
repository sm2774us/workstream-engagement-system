"""Pydantic domain models for WES Workstreams and Hermes documents."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkstreamStatus(str, Enum):
    """Lifecycle state of a Workstream task."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    BLOCKED = "blocked"
    DONE = "done"


class Workstream(BaseModel):
    """A unit of engagement work tracked through WES.

    Attributes:
        id: Stable identifier.
        title: Short human-readable summary.
        status: Current lifecycle state.
        risk_score: Rust/Tonic-engine-computed priority/risk score (0-100).
        assignee: Entra ID `sub` claim of the assigned engineer.
        updated_at: Last mutation timestamp (UTC).
    """

    id: str
    title: str
    status: WorkstreamStatus = WorkstreamStatus.DRAFT
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    assignee: str | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkstreamEvent(BaseModel):
    """Event-driven payload published to Event Hubs / Kafka on mutation.

    Attributes:
        event_type: Discriminator for downstream consumers.
        workstream: The Workstream snapshot at event time.
        actor: Entra ID subject who triggered the mutation.
        emitted_at: UTC emission timestamp.
    """

    event_type: str
    workstream: Workstream
    actor: str
    emitted_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """A retrieval-augmented-generation chunk indexed from a Hermes document.

    Mirrors the shape expected by Azure AI Search + HelixDB hybrid
    retrieval: dense vector for semantic search, sparse fields for
    keyword/BM25 fallback.
    """

    chunk_id: str
    document_id: str
    text: str
    embedding: list[float] = Field(default_factory=list)
    source_uri: str | None = None
