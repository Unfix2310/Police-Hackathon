from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(tags=["Investigation"])

@router.get("/graph/{entity_type}/{entity_id}")
async def get_investigation_graph(
    entity_type: str,
    entity_id: str,
    depth: int = 1,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Get investigation graph neighbors (NetworkX mapping)."""
    return {"nodes": [], "edges": []}

@router.get("/graph/{entity_type}/{entity_id}/path")
async def get_graph_path(
    entity_type: str,
    entity_id: str,
    target_type: str,
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Find connection path between two entities."""
    return []

@router.get("/timeline/{entity_type}/{entity_id}")
async def get_timeline(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Chronological timeline events."""
    return []
