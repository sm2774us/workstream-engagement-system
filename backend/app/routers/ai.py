"""AI-integrated endpoints: RAG search over Hermes documents (WES JD 'AI-Integrated Application Development')."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.security import Principal, get_current_principal
from app.models.workstream import DocumentChunk
from app.services.rag import RetrievalGateway, get_retrieval_gateway

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.get("/search", response_model=list[DocumentChunk])
async def semantic_search(
    q: str,
    top_k: int = 5,
    principal: Principal = Depends(get_current_principal),
    gateway: RetrievalGateway = Depends(get_retrieval_gateway),
) -> list[DocumentChunk]:
    """Hybrid semantic + keyword search over indexed Hermes chunks."""
    return await gateway.search(q, top_k=top_k)


async def _stream_answer(query: str, chunks: list[DocumentChunk]):
    """Yield a token-streamed answer, grounded in retrieved chunks.

    Mirrors the JD requirement to "build ... streaming response handlers
    that surface AI features reliably": this simulates an LLM token
    stream through the TensorZero-style gateway without requiring a
    live model API key for the showcase to run.
    """
    preamble = f"Answering '{query}' using {len(chunks)} retrieved chunk(s):\n"
    for token in preamble.split(" "):
        yield token + " "
    for chunk in chunks:
        for token in chunk.text.split(" "):
            yield token + " "
        yield "\n"


@router.get("/ask")
async def ask(
    q: str,
    principal: Principal = Depends(get_current_principal),
    gateway: RetrievalGateway = Depends(get_retrieval_gateway),
) -> StreamingResponse:
    """RAG-grounded, streamed answer endpoint (Server-Sent-Events style)."""
    chunks = await gateway.search(q, top_k=3)
    return StreamingResponse(_stream_answer(q, chunks), media_type="text/plain")
