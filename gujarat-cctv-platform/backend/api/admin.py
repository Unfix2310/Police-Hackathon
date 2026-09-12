import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth.jwt import create_access_token
from auth.rbac import get_current_user
from models.user import User

router = APIRouter(tags=["Admin"])

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.get("/health")
async def health_check():
    """System health check."""
    return {"status": "healthy", "version": "1.0.0"}

@router.post("/auth/token")
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT access token."""
    username = form_data.username.strip()
    
    # 1. Match by badge_number, user_id, or role
    result = await db.execute(
        select(User).where(
            (User.badge_number.ilike(username)) |
            (User.user_id.ilike(username)) |
            (User.role.ilike(username))
        )
    )
    user = result.scalars().first()
    
    # 2. Fallback for generic demo usernames
    if not user:
        role_map = {
            "admin": "admin",
            "administrator": "admin",
            "demo_user": "admin",
            "operator": "operator",
            "investigator": "investigator",
            "command": "command",
        }
        target_role = role_map.get(username.lower())
        if target_role:
            result = await db.execute(select(User).where(User.role == target_role))
            user = result.scalars().first()
            
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not user.password_hash or not secrets.compare_digest(user.password_hash, _hash_password(form_data.password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    token = create_access_token({
        "sub": user.user_id,
        "role": user.role,
        "badge": user.badge_number,
        "name": user.full_name,
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "role": user.role,
            "badge_number": user.badge_number,
            "district": user.district,
        }
    }

@router.get("/auth/me")
async def get_me(
    user: dict = Depends(get_current_user)
):
    """Get current user details from JWT."""
    return user

@router.get("/audit")
async def get_audit_logs(
    user: dict = Depends(get_current_user)
):
    """Query system audit logs."""
    return []
