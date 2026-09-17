"""Retrieval-augmented generation over Hermes documents.

Models the hybrid-retrieval pattern the JD calls out: Azure AI Search
for managed vector + keyword indexing, HelixDB as a lower-latency
self-hosted vector store for hot document sets, and a TensorZero-style
gateway in front of the underlying LLM calls so prompt/model routing,
caching, and evaluation are decoupled from application code.

All three integrations are modeled behind one `RetrievalGateway`
interface with an in-memory cosine-similarity implementation so the
showcase runs offline; swapping in the managed services is an adapter
change, not a rewrite of the calling code in `routers/ai.py`.
"""
from __future__ import annotations

import math
from typing import Protocol

from app.models.workstream import DocumentChunk


class RetrievalGateway(Protocol):
    """Resolves the top-k most relevant chunks for a query embedding."""

    async def search(self, query: str, top_k: int = 5) -> list[DocumentChunk]:
        ...


def _fake_embed(text: str, dims: int = 32) -> list[float]:
    """Deterministic bag-of-hashes embedding stand-in for offline demo use.

    A real deployment calls an embedding model through the TensorZero
    gateway (`POST /v1/embeddings`), which handles provider routing and
    response caching centrally.
    """
    vec = [0.0] * dims
    for token in text.lower().split():
        vec[hash(token) % dims] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


class InMemoryHybridGateway:
    """Offline stand-in for Azure AI Search + HelixDB hybrid retrieval.

    Combines dense cosine similarity (semantic) with a simple substring
    match boost (keyword/BM25 stand-in) to mirror hybrid ranking.
    """

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def index(self, chunk: DocumentChunk) -> None:
        if not chunk.embedding:
            chunk.embedding = _fake_embed(chunk.text)
        self._chunks.append(chunk)

    async def search(self, query: str, top_k: int = 5) -> list[DocumentChunk]:
        query_vec = _fake_embed(query)
        scored = []
        for chunk in self._chunks:
            semantic = _cosine(query_vec, chunk.embedding)
            keyword_boost = 0.15 if query.lower() in chunk.text.lower() else 0.0
            scored.append((semantic + keyword_boost, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]


_gateway_singleton = InMemoryHybridGateway()
_gateway_singleton.index(
    DocumentChunk(
        chunk_id="c1",
        document_id="hermes-onboarding",
        text="WES Workstreams route approvals through Hermes for document intelligence.",
    )
)
_gateway_singleton.index(
    DocumentChunk(
        chunk_id="c2",
        document_id="hermes-risk-policy",
        text="Blocked Workstreams above a risk threshold require senior engineer sign-off.",
    )
)


def get_retrieval_gateway() -> RetrievalGateway:
    """Return the process-wide retrieval gateway singleton."""
    return _gateway_singleton
