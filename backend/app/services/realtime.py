"""Real-time fan-out: Azure SignalR Service (serverless mode) bridge.

In Azure SignalR's *serverless* mode, the API doesn't hold persistent
client sockets itself -- it POSTs to the SignalR Service REST/negotiate
endpoints and the managed service owns the actual WebSocket fan-out to
browsers. That is the production path (`AzureSignalRBroadcaster`).

For the showcase to run without an Azure subscription, a native FastAPI
WebSocket hub (`LocalWebSocketHub`) implements the identical
`RealtimeBroadcaster` interface, so swapping to Azure SignalR in a real
KR deployment is a one-line change at the composition root
(`app/main.py`), not a rewrite.
"""
from __future__ import annotations

import json
from typing import Protocol

from fastapi import WebSocket

from app.core.telemetry import get_logger
from app.models.workstream import WorkstreamEvent

logger = get_logger(__name__)


class RealtimeBroadcaster(Protocol):
    """Broadcasts a domain event to all connected real-time clients."""

    async def broadcast(self, event: WorkstreamEvent) -> None:
        ...


class AzureSignalRBroadcaster:
    """Broadcasts through Azure SignalR Service's REST management API.

    Uses the SignalR "hub" REST endpoint (`/api/v1/hubs/{hub}/:send`)
    secured by a short-lived JWT minted from the service connection
    string's access key -- the standard serverless integration pattern,
    avoiding any in-process socket management.
    """

    def __init__(self, connection_str: str, hub_name: str = "workstreams") -> None:
        self._connection_str = connection_str
        self._hub_name = hub_name

    def _parse_connection_string(self) -> dict[str, str]:
        parts = dict(kv.split("=", 1) for kv in self._connection_str.split(";") if kv)
        return parts

    async def broadcast(self, event: WorkstreamEvent) -> None:
        import time

        import httpx
        import jwt as pyjwt

        parts = self._parse_connection_string()
        endpoint = parts["Endpoint"].rstrip("/")
        access_key = parts["AccessKey"]
        audience = f"{endpoint}/api/v1/hubs/{self._hub_name.lower()}"
        token = pyjwt.encode(
            {"aud": audience, "exp": int(time.time()) + 60},
            access_key,
            algorithm="HS256",
        )
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{audience}/:send",
                params={"api-version": "2022-11-01"},
                headers={"Authorization": f"Bearer {token}"},
                json={"target": "workstreamUpdated", "arguments": [event.model_dump(mode="json")]},
            )
        logger.info("signalr.broadcast", event_type=event.event_type)


class LocalWebSocketHub:
    """In-process WebSocket hub used when no SignalR connection string is set.

    Mirrors the `{target, arguments}` message envelope SignalR clients
    expect, so the React `useSignalRLikeSocket` hook is transport-agnostic.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: WorkstreamEvent) -> None:
        payload = json.dumps(
            {"target": "workstreamUpdated", "arguments": [event.model_dump(mode="json")]}
        )
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001 - connection torn down client-side
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)
        logger.info("local_ws.broadcast", event_type=event.event_type, clients=len(self._connections))


_local_hub_singleton = LocalWebSocketHub()


def get_broadcaster(settings) -> RealtimeBroadcaster:
    """Select a broadcaster based on configuration; default to local hub."""
    if settings.signalr_connection_str:
        return AzureSignalRBroadcaster(settings.signalr_connection_str)
    return _local_hub_singleton


def get_local_hub() -> LocalWebSocketHub:
    """Return the process-wide local WebSocket hub (used by the router)."""
    return _local_hub_singleton
