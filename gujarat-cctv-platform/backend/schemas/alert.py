from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from models.enums import AlertType, IncidentSeverity

class AlertResponse(BaseModel):
    alert_id: str
    type: AlertType
    priority: IncidentSeverity
    timestamp: datetime
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    description: str
    linked_observation_id: Optional[UUID] = None
    status: str
    model_config = ConfigDict(from_attributes=True)

class AlertAcknowledge(BaseModel):
    status: str = "ACKNOWLEDGED"
