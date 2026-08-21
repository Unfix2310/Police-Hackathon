from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("")
async def list_incidents(
    status: Optional[str] = None,
    district: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator", "command"]))
):
    """List incidents."""
    return []

@router.post("")
async def create_incident(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator"]))
):
    """Create new incident."""
    return {"id": "new_inc_id"}

@router.patch("/{inc_id}")
async def update_incident(
    inc_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["operator", "investigator"]))
):
    """Update status or priority."""
    return {}
