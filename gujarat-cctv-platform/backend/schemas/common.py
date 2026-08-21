from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    size: int

class ErrorResponse(BaseModel):
    detail: str

class SuccessResponse(BaseModel):
    message: str
