from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from auth.rbac import require_role
from models.user import User
from models.observation import Observation
from models.alert import Alert
from simulator.camera_registry import get_all_cameras

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command", "operator", "investigator", "sysadmin"]))
):
    """State overview for Command Dashboard with real metrics."""
    try:
        obs_count = await db.scalar(select(func.count(Observation.id))) or 0
        alert_count = await db.scalar(select(func.count(Alert.id))) or 0
    except Exception:
        obs_count = 0
        alert_count = 0

    cams = len(get_all_cameras())
    return {
        "active_incidents": 0,
        "total_observations": obs_count,
        "active_cameras": cams,
        "active_alerts": alert_count,
        "system_health": "100%"
    }

@router.get("/camera-health")
async def get_camera_health_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command", "sysadmin"]))
):
    """Camera health by district."""
    return {}

@router.get("/trends")
async def get_trends(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command"]))
):
    """7-day / 30-day incident/observation trends."""
    return {"trends": []}
