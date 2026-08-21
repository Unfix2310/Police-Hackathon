from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])

@router.get("")
async def list_watchlists(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """List active watchlists."""
    return []

@router.post("")
async def create_watchlist(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Create watchlist."""
    return {"id": "new_wl_id"}

@router.post("/{list_id}/entries")
async def add_watchlist_entry(
    list_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Add entity to watchlist."""
    return {"id": "new_entry_id"}
