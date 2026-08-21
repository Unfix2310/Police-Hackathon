from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from models.enums import CaseStatus

class TimelineEntry(BaseModel):
    timestamp: datetime
    camera_id: str
    location_name: str
    confidence: float
    type: str
    description: str
    observations: List[UUID] = []

class CaseCreate(BaseModel):
    fir_reference: Optional[str] = None
    district: str
    police_station: str
    jurisdiction_code: str
    investigating_officer: str
    supervising_officer: str
    access_justification: str

class CaseLinkRequest(BaseModel):
    incident_ids: List[str] = []
    person_ids: List[str] = []
    vehicle_ids: List[str] = []
    observation_ids: List[UUID] = []

class CaseResponse(CaseCreate):
    case_id: str
    cctns_case_ref: Optional[str] = None
    assigned_date: datetime
    incidents: List[str] = []
    persons: List[str] = []
    vehicles: List[str] = []
    observations: List[UUID] = []
    cameras: List[str] = []
    timeline: List[TimelineEntry] = []
    evidence_packages: List[str] = []
    investigator_notes: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    access_list: List[str]
    classification: str = "RESTRICTED"
    status: CaseStatus = CaseStatus.OPEN
    created: datetime
    last_updated: datetime
    audit_trail: List[str] = []
    model_config = ConfigDict(from_attributes=True)
