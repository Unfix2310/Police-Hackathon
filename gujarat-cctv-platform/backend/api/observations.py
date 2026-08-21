from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/observations", tags=["Observations"])

@router.get("")
async def search_observations(
    start_time: str,
    end_time: str,
    camera_id: Optional[str] = None,
    type: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_meters: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Search raw canonical observations."""
    return {"observations": []}

@router.get("/{obs_id}")
async def get_observation(
    obs_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get details for a specific observation."""
    return {}

@router.post("")
async def create_observation(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["system"]))  # Internal system auth
):
    """Internal endpoint for the AI pipeline to create an observation."""
    return {"id": "new_obs_id"}
