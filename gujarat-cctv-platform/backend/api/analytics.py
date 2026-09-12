import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database import get_db
from auth.rbac import require_role
from models.user import User
from models.observation import Observation
from models.alert import Alert
from models.entity import Vehicle, Person
from models.incident import Incident
from models.camera import Camera
from simulator.camera_registry import get_all_cameras

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command", "operator", "investigator", "sysadmin"]))
):
    """State overview for Command Dashboard with real dynamic metrics."""
    try:
        obs_count = await db.scalar(select(func.count(Observation.observation_id))) or 0
        alert_count = await db.scalar(select(func.count(Alert.alert_id))) or 0
        vehicle_count = await db.scalar(select(func.count(Vehicle.vehicle_id))) or 0
        person_count = await db.scalar(select(func.count(Person.person_id))) or 0
        active_incidents = await db.scalar(
            select(func.count(Incident.incident_id)).where(
                Incident.status.in_(["OPEN", "IN_PROGRESS", "ACTIVE", "DISPATCHED", "PENDING"])
            )
        ) or 0
    except Exception as exc:
        logger.error("Failed to query overview analytics metrics from database: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics overview")

    all_cams = get_all_cameras()
    total_cams = len(all_cams)
    active_stream_count = 0
    try:
        from engine.stream_manager import get_stream_manager
        active_stream_count = len(get_stream_manager().get_active_streams())
    except Exception:
        active_stream_count = total_cams

    if total_cams > 0 and active_stream_count > 0:
        health_score = min(100.0, round((active_stream_count / total_cams) * 100, 1))
        system_health = f"{health_score}%"
    elif total_cams > 0:
        system_health = "STANDBY"
    else:
        system_health = "100%"

    return {
        "active_incidents": active_incidents,
        "total_observations": obs_count,
        "active_cameras": total_cams,
        "active_streams": active_stream_count,
        "active_alerts": alert_count,
        "system_health": system_health,
        "total_vehicles": vehicle_count,
        "total_persons": person_count
    }

@router.get("/camera-health")
async def get_camera_health_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command", "sysadmin"]))
):
    """Camera health grouped by district."""
    all_cams = get_all_cameras()
    active_stream_set = set()
    try:
        from engine.stream_manager import get_stream_manager
        active_stream_set = set(get_stream_manager().get_active_streams())
    except Exception:
        pass

    district_map: Dict[str, Dict[str, Any]] = {}
    for cam in all_cams:
        d = cam.get("district", "Unassigned")
        c_id = cam.get("cam_id", "")
        entry = district_map.setdefault(d, {"district": d, "total": 0, "online": 0, "offline": 0, "health_pct": 100.0})
        entry["total"] += 1
        if not active_stream_set or c_id in active_stream_set:
            entry["online"] += 1
        else:
            entry["offline"] += 1

    for d, data in district_map.items():
        if data["total"] > 0:
            data["health_pct"] = round((data["online"] / data["total"]) * 100, 1)

    return {"districts": list(district_map.values())}

@router.get("/trends")
async def get_trends(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command"]))
):
    """Daily incident and observation trends over requested window."""
    now = datetime.now(timezone.utc)
    trends = []
    try:
        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            date_str = day_start.strftime("%Y-%m-%d")

            inc_stmt = select(func.count(Incident.incident_id)).where(
                and_(Incident.created_at >= day_start, Incident.created_at < day_end)
            )
            obs_stmt = select(func.count(Observation.observation_id)).where(
                and_(Observation.timestamp_capture >= day_start, Observation.timestamp_capture < day_end)
            )

            inc_count = await db.scalar(inc_stmt) or 0
            obs_count = await db.scalar(obs_stmt) or 0

            trends.append({
                "date": date_str,
                "incidents": inc_count,
                "observations": obs_count
            })
    except Exception as exc:
        logger.error("Failed to query analytics trends: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics trends")

    return {"trends": trends}
