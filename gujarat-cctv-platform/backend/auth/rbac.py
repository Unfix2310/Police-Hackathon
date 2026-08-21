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

def require_role(roles: List[UserRoleEnum]) -> Callable:
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker
