from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("")
async def list_cameras(
    district: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    capability: Optional[str] = Query(None),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator", "command", "sysadmin"]))
):
    """List cameras in the system."""
    return {"cameras": [], "total": 0}

@router.get("/health/summary")
async def camera_health_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["command", "sysadmin"]))
):
    """Get aggregate health statistics."""
    return {"total": 0, "online": 0, "offline": 0, "degraded": 0, "by_district": {}}

@router.get("/{cam_id}")
async def get_camera(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator", "command", "sysadmin"]))
):
    """Get details for a specific camera."""
    return {}

@router.get("/{cam_id}/health")
async def get_camera_health(
    cam_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "command", "sysadmin"]))
):
    """Get health telemetry for a specific camera."""
    return {}
