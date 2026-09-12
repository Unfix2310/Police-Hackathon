"""
WebSocket & SSE endpoints for real-time alert push and live observation streaming.

Connected clients are registered in a global set. When the alert broadcaster
(see `broadcast_alert`) is called from the pipeline or watchlist engine,
all connected WebSocket clients receive the alert JSON immediately.
"""

from fastapi import APIRouter, WebSocket, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Set

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])

# ── Global client registry ────────────────────────────────────────────────────

_alert_clients: Set[WebSocket] = set()
_camera_clients: Set[WebSocket] = set()


async def broadcast_alert(alert_data: dict):
    """
    Broadcast an alert to all connected WebSocket clients.
    Call this from the watchlist engine or entity resolver when an alert is generated.
    """
    if not _alert_clients:
        return

    message = json.dumps(alert_data, default=str)
    disconnected = set()

    for ws in _alert_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)

    _alert_clients.difference_update(disconnected)
    if disconnected:
        logger.debug(f"Cleaned up {len(disconnected)} disconnected alert clients")


async def broadcast_camera_status(status_data: dict):
    """
    Broadcast camera status updates to all connected WebSocket clients.
    """
    if not _camera_clients:
        return

    message = json.dumps(status_data, default=str)
    disconnected = set()

    for ws in _camera_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)

    _camera_clients.difference_update(disconnected)


# ── WebSocket endpoints ───────────────────────────────────────────────────────

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Real-time push of generated alerts."""
    await websocket.accept()
    _alert_clients.add(websocket)
    logger.info(f"Alert WebSocket client connected. Total: {len(_alert_clients)}")
    try:
        while True:
            # Keep connection alive; respond to client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
    except Exception:
        pass
    finally:
        _alert_clients.discard(websocket)
        logger.info(f"Alert WebSocket client disconnected. Remaining: {len(_alert_clients)}")


@router.websocket("/ws/cameras")
async def websocket_cameras(websocket: WebSocket):
    """Camera status heartbeat stream."""
    await websocket.accept()
    _camera_clients.add(websocket)
    logger.info(f"Camera WebSocket client connected. Total: {len(_camera_clients)}")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
    except Exception:
        pass
    finally:
        _camera_clients.discard(websocket)


@router.get("/api/v1/observations/stream")
async def observations_stream():
    """Server-Sent Events for live observation ticker."""
    async def event_generator():
        while True:
            yield "data: {\"event\": \"ping\"}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
