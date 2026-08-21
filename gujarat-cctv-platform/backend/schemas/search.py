from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.enums import ObservationType

class SearchRequest(BaseModel):
    query: Optional[str] = None
    observation_type: Optional[ObservationType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    camera_ids: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    limit: int = 100
    offset: int = 0

class SearchResponse(BaseModel):
    results: List[Any] # Can be ObservationResponse, PersonResponse, VehicleResponse
    total: int

class SceneRequest(BaseModel):
    camera_id: str
    timestamp: datetime
    window_minutes: int = 5
