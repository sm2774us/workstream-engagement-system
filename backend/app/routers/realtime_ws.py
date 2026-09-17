"""Local WebSocket endpoint standing in for Azure SignalR in serverless mode.

React clients connect here directly when `VITE_SIGNALR_MODE=local`;
against a real Azure SignalR Service, clients instead call
`POST /api/v1/realtime/negotiate` to obtain a service-issued URL/token
and connect to Azure directly, bypassing this API entirely (the
serverless pattern). Both paths are implemented so the diagram in the
README is fully backed by code.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.config import Settings, get_settings
from app.services.realtime import get_local_hub

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])


@router.get("/negotiate")
async def negotiate(settings: Settings = Depends(get_settings)) -> dict:
    """Return connection info, mirroring the Azure SignalR negotiate contract.

    Against real Azure SignalR this endpoint would mint a short-lived
    access token via the service connection string and return the
    service's own hub URL, per the documented negotiate response shape.
    """
    if settings.signalr_connection_str:
        return {"mode": "azure-signalr", "url": "<issued-by-azure-signalr>", "accessToken": "<jwt>"}
    return {"mode": "local-websocket", "url": "/api/v1/realtime/ws", "accessToken": None, "issuedAt": time.time()}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Local dev/demo WebSocket hub matching the SignalR message envelope."""
    hub = get_local_hub()
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # heartbeat/no-op from client
    except WebSocketDisconnect:
        hub.disconnect(websocket)
