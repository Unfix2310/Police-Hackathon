from fastapi import Depends, HTTPException, status
from typing import List, Callable
from .jwt import verify_token
from models.enums import UserRoleEnum

def get_current_user(payload: dict = Depends(verify_token)) -> dict:
    # Here we typically fetch the user from the DB using payload subject.
    # Returning payload mock for now.
    user = {
        "user_id": payload.get("sub"),
        "role": payload.get("role", UserRoleEnum.OPERATOR.value)
    }
    if not user["user_id"]:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

def require_role(roles: List[str]) -> Callable:
    def role_checker(current_user: dict = Depends(get_current_user)):
        # Handle both Enum and string inputs from routers
        allowed_roles = [r.value if hasattr(r, 'value') else r for r in roles]
        user_role = current_user.get("role")
        user_role_val = user_role.value if hasattr(user_role, 'value') else user_role
        
        if user_role_val not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker
