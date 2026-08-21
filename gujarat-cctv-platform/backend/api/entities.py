from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/entities", tags=["Entities"])

@router.get("/vehicles")
async def search_vehicles(
    plate: Optional[str] = None,
    color: Optional[str] = None,
    type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Search for vehicle entities."""
    return []

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get unified vehicle entity details."""
    return {}

@router.get("/vehicles/{vehicle_id}/trajectory")
async def get_vehicle_trajectory(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get spatial trajectory of a vehicle."""
    return {"points": []}

@router.get("/persons")
async def search_persons(
    gender: Optional[str] = None,
    clothing_color: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Search for person entities."""
    return []

@router.get("/persons/{person_id}")
async def get_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get person details + recent observations."""
    return {}
