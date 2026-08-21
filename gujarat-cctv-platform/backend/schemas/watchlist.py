from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from models.enums import ObservationType, IncidentSeverity

class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WatchlistEntryCreate(BaseModel):
    type: ObservationType
    entity_id: str
    reason: str
    priority: IncidentSeverity
    expiry: Optional[datetime] = None

class WatchlistResponse(WatchlistCreate):
    watchlist_id: str
    owner_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
