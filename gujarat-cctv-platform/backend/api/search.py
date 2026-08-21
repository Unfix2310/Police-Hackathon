from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("")
async def unified_search(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Unified semantic/attribute search."""
    return {"results": []}

@router.post("/scene")
async def reconstruct_scene(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Reconstruct a scene (all entities in radius at time)."""
    return {}
