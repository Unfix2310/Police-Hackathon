from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role

router = APIRouter(prefix="/investigation", tags=["Investigation"])

@router.get("/graph/{entity_type}/{entity_id}")
async def get_investigation_graph(
    entity_type: str,
    entity_id: str,
    depth: int = 1,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator", "command"]))
):
    """Get investigation graph neighbors (NetworkX mapping). Stub — use /graph/ for real temporal graph."""
    return {"nodes": [], "edges": [], "_note": "Use GET /api/v1/graph/{entity_type}/{entity_id} for real temporal graph data."}

@router.get("/graph/{entity_type}/{entity_id}/path")
async def get_graph_path(
    entity_type: str,
    entity_id: str,
    target_type: str = "",
    target_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator", "command"]))
):
    """Find connection path between two entities."""
    return []

@router.get("/timeline/{entity_type}/{entity_id}")
async def get_timeline(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator", "command"]))
):
    """Chronological timeline events."""
    return []
