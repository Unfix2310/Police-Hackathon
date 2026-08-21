from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("")
async def list_cases(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """List cases."""
    return []

@router.post("")
async def create_case(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Create case."""
    return {"id": "new_case_id"}

@router.get("/{case_id}")
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Case detail."""
    return {}

@router.post("/{case_id}/link")
async def link_to_case(
    case_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Link an observation or entity to a case."""
    return {}
