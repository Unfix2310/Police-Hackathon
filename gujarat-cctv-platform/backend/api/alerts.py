from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "command"]))
):
    """List active unacknowledged alerts."""
    return []

@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator"]))
):
    """Acknowledge an alert."""
    return {}
