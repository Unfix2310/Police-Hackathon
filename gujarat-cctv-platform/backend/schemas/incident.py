from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from models.enums import IncidentSeverity

class IncidentCreate(BaseModel):
    type: str
    severity: IncidentSeverity
    location_lat: float
    location_lng: float
    start_time: datetime
    description: str

class IncidentUpdate(BaseModel):
    severity: Optional[IncidentSeverity] = None
    status: Optional[str] = None
    end_time: Optional[datetime] = None

class IncidentResponse(IncidentCreate):
    incident_id: str
    status: str
    end_time: Optional[datetime] = None
    observations: List[UUID] = []
    model_config = ConfigDict(from_attributes=True)
