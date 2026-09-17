"""Client for the Rust/Axum/Tonic performance-critical risk-scoring engine.

WES's business logic lives in Python/FastAPI, but risk-scoring a
Workstream requires scanning large historical event windows under tight
latency budgets -- a workload better suited to Rust. The Rust service
exposes both a Tonic gRPC endpoint (used here, for typed, low-overhead
internal calls) and an Axum HTTP endpoint (used by non-gRPC tooling,
see `rust-engine/src/http.rs`), demonstrating the dual-protocol pattern
KR's JD calls out explicitly (Axum *and* Tonic).

This client degrades to a local heuristic when the Rust engine isn't
running, so the Python side of the showcase works standalone.
"""
from __future__ import annotations

from app.core.telemetry import get_logger

logger = get_logger(__name__)


class RustEngineClient:
    """Thin async client over the Tonic gRPC risk-scoring service."""

    def __init__(self, grpc_target: str) -> None:
        self._grpc_target = grpc_target

    async def score_workstream(self, title: str, status: str) -> float:
        """Return a 0-100 risk score computed by the Rust engine.

        Falls back to a deterministic local heuristic (matching the
        Rust service's own fallback formula, see `risk.rs`) if the gRPC
        channel cannot be established, so the API stays available
        during a Rust-engine rollout or outage.
        """
        try:
            return await self._score_via_grpc(title, status)
        except Exception as exc:  # noqa: BLE001 - network/engine unavailable
            logger.warning("rust_engine.fallback", error=str(exc))
            return self._local_heuristic(title, status)

    async def _score_via_grpc(self, title: str, status: str) -> float:
        import grpc

        # Generated stubs (`risk_pb2*.py`) are produced at build time from
        # `rust-engine/proto/risk.proto` via `python -m grpc_tools.protoc`
        # (see Makefile target `proto`). Imported lazily so the showcase
        # doesn't hard-fail when stubs haven't been generated yet.
        from app.generated import risk_pb2, risk_pb2_grpc  # type: ignore

        async with grpc.aio.insecure_channel(self._grpc_target) as channel:
            stub = risk_pb2_grpc.RiskEngineStub(channel)
            response = await stub.ScoreWorkstream(
                risk_pb2.ScoreRequest(title=title, status=status)
            )
            return response.score

    @staticmethod
    def _local_heuristic(title: str, status: str) -> float:
        base = min(len(title) * 1.5, 60.0)
        status_weight = {
            "draft": 5.0,
            "in_review": 25.0,
            "approved": 10.0,
            "blocked": 40.0,
            "done": 0.0,
        }.get(status, 15.0)
        return round(min(base + status_weight, 100.0), 2)
