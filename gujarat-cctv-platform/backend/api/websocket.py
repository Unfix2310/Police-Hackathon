from fastapi import APIRouter, WebSocket, Depends
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Real-time push of generated alerts."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Received: {data}")
    except Exception:
        pass

@router.websocket("/ws/cameras")
async def websocket_cameras(websocket: WebSocket):
    """Camera status heartbeat stream."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Heartbeat: {data}")
    except Exception:
        pass

@router.get("/api/v1/observations/stream")
async def observations_stream():
    """Server-Sent Events for live observation ticker."""
    async def event_generator():
        while True:
            yield "data: {\"event\": \"ping\"}\n\n"
            await asyncio.sleep(5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
