from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from models.enums import ObservationType, VehicleClass, IncidentSeverity

class ObservationPayloadPerson(BaseModel):
    clothing: str
    bag: Optional[str] = None
    helmet: bool = False
    gender_estimate: Optional[str] = None

class ObservationPayloadVehicle(BaseModel):
    plate: Optional[str] = None
    plate_confidence: Optional[float] = None
    color: Optional[str] = None
    vehicle_class: VehicleClass = VehicleClass.UNKNOWN
    make_model: Optional[str] = None

class ObservationPayloadEvent(BaseModel):
    event_type: str
    severity: IncidentSeverity
    details: Dict[str, Any] = {}

class ObservationBase(BaseModel):
    observation_id: UUID
    observation_type: ObservationType
    source_camera_id: str
    source_gateway_id: str
    source_edge_id: str
    timestamp_capture: datetime
    timestamp_process: datetime
    location_lat: float
    location_lng: float
    bounding_box: List[int] = Field(..., min_length=4, max_length=4)
    track_id: str
    confidence: float
    payload: Dict[str, Any]
    feature_vector_ref: Optional[str] = None
    frame_ref: str
    video_ref: str
    frame_offset_ms: int
    crop_ref: Optional[str] = None
    model_id: str
    model_version: str
    model_hash: str
    processing_node: str
    processing_latency: int
    observation_hash: str

class ObservationCreate(ObservationBase):
    pass

class ObservationResponse(ObservationBase):
    model_config = ConfigDict(from_attributes=True)
