from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.post("/generate")
async def generate_evidence(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator"]))
):
    """Generate verifiable Sec 65B evidence package."""
    raise HTTPException(
        status_code=501,
        detail="Evidence package generation is not yet implemented. "
               "Real SHA-256 manifest and Section 65B certification "
               "requires validated chain-of-custody implementation."
    )

@router.get("/{evidence_id}")
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["investigator"]))
):
    """Get completed evidence package metadata."""
    raise HTTPException(
        status_code=501,
        detail="Evidence retrieval is not yet implemented."
    )
