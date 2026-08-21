from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from models.enums import EntityStatus, VehicleClass, FeasibilityLabel
from .observation import ObservationPayloadPerson, ObservationPayloadVehicle

class PersonResponse(BaseModel):
    person_id: str
    first_seen: datetime
    last_seen: datetime
    observation_count: int
    observation_ids: List[UUID]
    running_confidence: float
    attributes: ObservationPayloadPerson
    watchlist_matches: List[str] = []
    status: EntityStatus
    model_config = ConfigDict(from_attributes=True)

class VehicleResponse(BaseModel):
    vehicle_id: str
    plate: Optional[str] = None
    plate_confidence: Optional[float] = None
    color: Optional[str] = None
    vehicle_class: VehicleClass = VehicleClass.UNKNOWN
    make_model: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    observation_count: int
    observation_ids: List[UUID]
    associated_persons: List[str] = []
    watchlist_matches: List[str] = []
    status: EntityStatus
    model_config = ConfigDict(from_attributes=True)

class TrajectoryPoint(BaseModel):
    location_lat: float
    location_lng: float
    timestamp: datetime
    camera_id: str

class FeasibilityResult(BaseModel):
    score: float
    label: FeasibilityLabel
    required_speed_kmh: float
    road_distance_km: float
    road_class: str
    explanation: str

class TrajectoryResponse(BaseModel):
    vehicle_id: str
    points: List[TrajectoryPoint]
    distances: List[float]
    average_speed: float
    feasibility_score: float
    feasibility_label: FeasibilityLabel
