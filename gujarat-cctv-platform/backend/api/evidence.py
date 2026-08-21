from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.rbac import require_role
from models.user import User

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.post("/generate")
async def generate_evidence(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Generate verifiable Sec 65B evidence package."""
    return {"job_id": "ev_gen_888"}

@router.get("/{evidence_id}")
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Get completed evidence package metadata and download link."""
    return {"id": evidence_id, "status": "ready", "hash_sha256": "abc123def", "download_url": f"https://storage/{evidence_id}.zip"}
