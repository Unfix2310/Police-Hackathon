from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from auth.rbac import require_role
from models.observation import Observation
from models.camera import Camera
from models.enums import ObservationType
from api.correlation import haversine
from simulator.camera_registry import get_camera

router = APIRouter(prefix="/observations", tags=["Observations"])


def _parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        cleaned = dt_str.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except Exception:
        return None


@router.get("")
async def search_observations(
    start_time: Optional[str] = Query(None, description="Start timestamp in ISO 8601 format"),
    end_time: Optional[str] = Query(None, description="End timestamp in ISO 8601 format"),
    camera_id: Optional[str] = Query(None, description="Source camera ID"),
    type: Optional[str] = Query(None, description="Observation type (PERSON, VEHICLE, etc.)"),
    lat: Optional[float] = Query(None, description="Latitude for spatial radius search"),
    lon: Optional[float] = Query(None, description="Longitude for spatial radius search"),
    radius_meters: Optional[int] = Query(None, description="Search radius in meters from (lat, lon)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Records offset for pagination"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator", "command", "admin", "operator"]))
):
    """
    Search raw canonical observations with temporal, camera, type, and geographic radius filters.
    """
    limit_val = limit if isinstance(limit, int) else 100
    offset_val = offset if isinstance(offset, int) else 0
    start_time_val = start_time if isinstance(start_time, str) else None
    end_time_val = end_time if isinstance(end_time, str) else None
    camera_id_val = camera_id if isinstance(camera_id, str) else None
    type_val = type if isinstance(type, str) else None
    lat_val = lat if isinstance(lat, (int, float)) else None
    lon_val = lon if isinstance(lon, (int, float)) else None
    radius_val = radius_meters if isinstance(radius_meters, (int, float)) else None

    query = (
        select(Observation, Camera)
        .outerjoin(Camera, Observation.source_camera_id == Camera.cam_id)
    )

    parsed_start = _parse_iso_datetime(start_time_val)
    if parsed_start:
        query = query.where(Observation.timestamp_capture >= parsed_start)

    parsed_end = _parse_iso_datetime(end_time_val)
    if parsed_end:
        query = query.where(Observation.timestamp_capture <= parsed_end)

    if camera_id_val:
        query = query.where(Observation.source_camera_id == camera_id_val)

    if type_val:
        try:
            obs_type_enum = ObservationType(type_val.upper().strip())
            query = query.where(Observation.observation_type == obs_type_enum)
        except ValueError:
            query = query.where(Observation.observation_type == type_val.upper().strip())

    query = query.order_by(Observation.timestamp_capture.desc())

    result = await db.execute(query)
    rows = result.all()

    # Spatial radius filtering using haversine if lat/lon/radius_meters are provided
    filtered_rows = []
    for obs, cam in rows:
        cam_info = get_camera(obs.source_camera_id) if obs.source_camera_id else None
        cam_lat = cam.latitude if (cam and cam.latitude is not None) else (cam_info.get("lat") or cam_info.get("latitude") if cam_info else None)
        cam_lng = cam.longitude if (cam and cam.longitude is not None) else (cam_info.get("lng") or cam_info.get("longitude") if cam_info else None)

        if lat_val is not None and lon_val is not None and radius_val is not None:
            if cam_lat is None or cam_lng is None:
                continue
            dist_km = haversine(lat_val, lon_val, cam_lat, cam_lng)
            if (dist_km * 1000.0) > radius_val:
                continue

        filtered_rows.append((obs, cam, cam_lat, cam_lng))

    total = len(filtered_rows)
    paged = filtered_rows[offset_val : offset_val + limit_val]

    observations_out = []
    for obs, cam, cam_lat, cam_lng in paged:
        observations_out.append({
            "observation_id": obs.observation_id,
            "timestamp_capture": obs.timestamp_capture.isoformat() if obs.timestamp_capture else None,
            "observation_type": obs.observation_type.value if hasattr(obs.observation_type, "value") else str(obs.observation_type),
            "source_camera_id": obs.source_camera_id,
            "camera_name": cam.display_name if cam else (cam_info.get("name") if cam_info else None),
            "latitude": cam_lat,
            "longitude": cam_lng,
            "bounding_box": obs.bounding_box,
            "track_id": obs.track_id,
            "confidence": obs.confidence,
            "payload": obs.payload,
            "crop_ref": obs.crop_ref,
            "video_ref": obs.video_ref
        })

    return {
        "total": total,
        "limit": limit_val,
        "offset": offset_val,
        "observations": observations_out
    }


@router.get("/{obs_id}")
async def get_observation(
    obs_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator", "command", "admin", "operator"]))
):
    """
    Get full canonical details for a specific observation by ID.
    Returns 404 if the observation does not exist.
    """
    query = (
        select(Observation, Camera)
        .outerjoin(Camera, Observation.source_camera_id == Camera.cam_id)
        .where(Observation.observation_id == obs_id)
        .limit(1)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Observation '{obs_id}' not found")

    obs, cam = row
    cam_info = get_camera(obs.source_camera_id) if obs.source_camera_id else None
    cam_lat = cam.latitude if (cam and cam.latitude is not None) else (cam_info.get("lat") or cam_info.get("latitude") if cam_info else None)
    cam_lng = cam.longitude if (cam and cam.longitude is not None) else (cam_info.get("lng") or cam_info.get("longitude") if cam_info else None)

    return {
        "observation_id": obs.observation_id,
        "timestamp_capture": obs.timestamp_capture.isoformat() if obs.timestamp_capture else None,
        "observation_type": obs.observation_type.value if hasattr(obs.observation_type, "value") else str(obs.observation_type),
        "source_camera_id": obs.source_camera_id,
        "source_gateway_id": obs.source_gateway_id,
        "source_edge_id": obs.source_edge_id,
        "camera_name": cam.display_name if cam else (cam_info.get("name") if cam_info else None),
        "latitude": cam_lat,
        "longitude": cam_lng,
        "bounding_box": obs.bounding_box,
        "track_id": obs.track_id,
        "confidence": obs.confidence,
        "payload": obs.payload,
        "feature_vector_ref": obs.feature_vector_ref,
        "crop_ref": obs.crop_ref,
        "frame_ref": obs.frame_ref,
        "video_ref": obs.video_ref,
        "frame_offset_ms": obs.frame_offset_ms,
        "model_id": obs.model_id,
        "model_version": obs.model_version,
        "processing_node": obs.processing_node,
        "processing_latency_ms": obs.processing_latency_ms,
        "observation_hash": obs.observation_hash
    }


@router.post("")
async def create_observation(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["system", "admin", "investigator", "command", "operator"]))
):
    """
    Internal endpoint for the AI pipeline or authorized clients to persist a canonical observation.
    """
    obs_id = payload.get("observation_id") or payload.get("id") or f"obs-{uuid.uuid4()}"

    # Parse or default timestamp_capture
    raw_ts = payload.get("timestamp_capture")
    if isinstance(raw_ts, str):
        parsed_ts = _parse_iso_datetime(raw_ts)
        timestamp_capture = parsed_ts if parsed_ts else datetime.now(timezone.utc)
    elif isinstance(raw_ts, datetime):
        timestamp_capture = raw_ts
    else:
        timestamp_capture = datetime.now(timezone.utc)

    # Determine observation type
    raw_type = payload.get("observation_type") or payload.get("type", "VEHICLE")
    try:
        obs_type = ObservationType(str(raw_type).upper().strip())
    except Exception:
        obs_type = ObservationType.VEHICLE

    camera_id = payload.get("source_camera_id") or payload.get("camera_id") or "CAM-GJ-AHM-SG-001"

    new_obs = Observation(
        observation_id=obs_id,
        timestamp_capture=timestamp_capture,
        observation_type=obs_type,
        source_camera_id=camera_id,
        source_gateway_id=payload.get("source_gateway_id"),
        source_edge_id=payload.get("source_edge_id"),
        timestamp_process=datetime.now(timezone.utc),
        bounding_box=payload.get("bounding_box"),
        track_id=payload.get("track_id"),
        confidence=float(payload.get("confidence", 0.9)),
        payload=payload.get("payload") or payload.get("attributes"),
        feature_vector_ref=payload.get("feature_vector_ref"),
        frame_ref=payload.get("frame_ref"),
        video_ref=payload.get("video_ref"),
        frame_offset_ms=payload.get("frame_offset_ms"),
        crop_ref=payload.get("crop_ref"),
        model_id=payload.get("model_id"),
        model_version=payload.get("model_version"),
        model_hash=payload.get("model_hash"),
        processing_node=payload.get("processing_node"),
        processing_latency_ms=payload.get("processing_latency_ms"),
        observation_hash=payload.get("observation_hash"),
    )

    db.add(new_obs)
    await db.commit()

    return {
        "observation_id": new_obs.observation_id,
        "id": new_obs.observation_id,
        "status": "created"
    }

