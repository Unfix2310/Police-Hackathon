from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from .case import TimelineEntry

class EvidenceGenerateRequest(BaseModel):
    case_reference: str
    purpose: str
    observation_ids: List[UUID]

class EvidenceResponse(BaseModel):
    package_id: str
    case_reference: str
    fir_reference: Optional[str] = None
    generated_by: str
    generated_at: datetime
    package_hash: str
    purpose: str
    timeline: List[TimelineEntry]
    trajectory_validation: Dict[str, Any]
    associated_persons: List[str]
    video_clips: List[Dict[str, str]]
    metadata: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)
