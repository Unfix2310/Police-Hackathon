from pydantic import BaseModel, ConfigDict
from typing import Optional
from models.enums import UserRoleEnum

class LoginRequest(BaseModel):
    badge_number: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    user_id: str
    role: UserRoleEnum
    name: str
    badge_id: Optional[str] = None
    district: str
    police_station: Optional[str] = None
    email: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
