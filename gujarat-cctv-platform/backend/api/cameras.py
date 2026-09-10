import asyncio
import logging
from typing import Dict, List, Optional
import httpx
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from auth.rbac import require_role
from models.user import User
from models.camera import Camera
from config import settings
from simulator.camera_registry import get_all_cameras

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["Cameras"])

_sentinel_client: Optional[httpx.AsyncClient] = None
_sentinel_lock = asyncio.Lock()
_key_cache: Dict[str, bytes] = {}

async def _login_sentinel(client: httpx.AsyncClient) -> bool:
    login_url = f"{settings.SENTINEL_CDN_HOST}/auth/login"
    try:
        resp = await client.post(
            login_url,
            data={
                "email": settings.SENTINEL_EMAIL,
                "password": settings.SENTINEL_PASSWORD
            }
        )
        return resp.status_code in (200, 302)
    except Exception as e:
        logger.error(f"Error logging in to Sentinel CDN: {e}")
        return False

async def _get_sentinel_client() -> httpx.AsyncClient:
    global _sentinel_client
    async with _sentinel_lock:
        if _sentinel_client is None or _sentinel_client.is_closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            client = httpx.AsyncClient(
                headers=headers,
                follow_redirects=False,
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
            )
            await _login_sentinel(client)
            _sentinel_client = client
        return _sentinel_client

def _serialize_cam(c: Camera) -> dict:
    stream_path = f"/api/v1/cameras/{c.cam_id}/stream/index.m3u8"
    loc = getattr(c, "location", None) or c.police_station or c.display_name
    return {
        "cam_id": c.cam_id,
        "display_name": c.display_name,
        "location": loc,
        "location_type": c.location_type or "Junction",
        "district": c.district or "Ahmedabad",
        "police_station": c.police_station or loc or "Unknown",
        "status": getattr(c.status, "value", str(c.status)),
        "rtsp_url": c.rtsp_url or settings.get_rtsp_url(c.cam_id),
        "hls_url": stream_path,
        "webrtc_url": settings.get_webrtc_url(c.cam_id),
        "web_url": stream_path,
        "direction_deg": c.direction_deg,
        "jurisdiction_code": c.jurisdiction_code,
    }

@router.get("")
async def list_cameras(
    district: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator", "command", "sysadmin"]))
):
    """List cameras in the system."""
    query = select(Camera)
    if district:
        query = query.where(Camera.district == district)
    
    total_query = select(func.count(Camera.cam_id))
    total_res = await db.execute(total_query)
    total = total_res.scalar() or 0
    
    res = await db.execute(query.offset(offset).limit(limit))
    cams = res.scalars().all()
    
    # Fallback to local registry if DB is empty
    if not cams:
        reg_cams = get_all_cameras()
        return {"cameras": reg_cams[offset:offset + limit], "total": len(reg_cams)}
        
    return {"cameras": [_serialize_cam(c) for c in cams], "total": total}

@router.get("/health/summary")
async def camera_health_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command", "sysadmin"]))
):
    """Get aggregate health statistics."""
    res = await db.execute(select(Camera))
    cams = res.scalars().all()
    if not cams:
        total = len(get_all_cameras())
        return {"total": total, "online": total, "offline": 0, "degraded": 0, "by_district": {}}
        
    online = sum(1 for c in cams if getattr(c.status, "value", str(c.status)).upper() in ("ONLINE", "ACTIVE"))
    by_district = {}
    for c in cams:
        dist = c.district or "Unknown"
        by_district[dist] = by_district.get(dist, 0) + 1
        
    return {
        "total": len(cams),
        "online": online,
        "offline": len(cams) - online,
        "degraded": 0,
        "by_district": by_district
    }

@router.get("/{cam_id}")
async def get_camera(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator", "command", "sysadmin"]))
):
    """Get details for a specific camera."""
    res = await db.execute(select(Camera).where(Camera.cam_id == cam_id))
    cam = res.scalar_one_or_none()
    if cam:
        return _serialize_cam(cam)
    
    # Fallback registry lookup
    for c in get_all_cameras():
        if c["cam_id"] == cam_id:
            return c
            
    raise HTTPException(status_code=404, detail=f"Camera {cam_id} not found")

@router.get("/{cam_id}/health")
async def get_camera_health(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "command", "sysadmin"]))
):
    """Get health telemetry for a specific camera."""
    return {"cam_id": cam_id, "status": "ONLINE", "stream_latency_ms": 120, "fps": 25, "packet_loss_pct": 0.0}


@router.get("/{cam_id}/stream/index.m3u8")
@router.get("/{cam_id}/stream.m3u8")
async def get_camera_stream_playlist(cam_id: str):
    """
    Proxies and authenticates HLS playlist from Sentinel CDN so browser video players
    do not require entering email/password.
    """
    client = await _get_sentinel_client()
    url = f"{settings.SENTINEL_CDN_HOST}/{cam_id}/index.m3u8"
    
    try:
        resp = await client.get(url)
        if resp.status_code in (302, 401, 403):
            await _login_sentinel(client)
            resp = await client.get(url)
            
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Stream playlist unavailable from Sentinel CDN")
            
        content = resp.text
        content = content.replace('URI="/enc.key"', 'URI="enc.key"')
        
        return Response(
            content=content,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to proxy playlist for {cam_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch stream: {str(e)}")


@router.get("/{cam_id}/stream/{file_name}")
async def get_camera_stream_asset(cam_id: str, file_name: str):
    """
    Proxies stream chunks (.ts) and encryption keys (.key) authenticated with Sentinel credentials.
    """
    client = await _get_sentinel_client()
    
    if file_name == "enc.key":
        if "enc.key" in _key_cache:
            return Response(
                content=_key_cache["enc.key"],
                media_type="application/octet-stream",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        target_url = f"{settings.SENTINEL_CDN_HOST}/enc.key"
        media_type = "application/octet-stream"
    else:
        target_url = f"{settings.SENTINEL_CDN_HOST}/{cam_id}/{file_name}"
        media_type = "video/mp2t"
        
    try:
        resp = await client.get(target_url)
        if resp.status_code in (302, 401, 403):
            await _login_sentinel(client)
            resp = await client.get(target_url)
            
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Asset {file_name} unavailable")
            
        if file_name == "enc.key":
            _key_cache["enc.key"] = resp.content
            
        return Response(
            content=resp.content,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=86400" if file_name.endswith(".ts") else "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to proxy asset {file_name} for {cam_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch asset: {str(e)}")

