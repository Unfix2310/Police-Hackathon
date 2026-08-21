from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from models.enums import CameraStatus, CameraType, CapabilityQuality

class CameraCapabilities(BaseModel):
    anpr: CapabilityQuality = Field(...)
    ptz: bool = Field(False)
    audio: bool = Field(False)
    person_detection: CapabilityQuality = Field(...)
    vehicle_detection: CapabilityQuality = Field(...)
    night_vision: CapabilityQuality = Field(...)
    crowd_estimation: CapabilityQuality = Field(...)
    speed_estimation: bool = Field(False)
    direction_detection: CapabilityQuality = Field(...)

class CameraBase(BaseModel):
    cam_id: str = Field(..., pattern=r"^CAM-[A-Z]{2}-[A-Z]{3}-.+$")
    external_cam_id: Optional[str] = None
    display_name: str
    owner_department: str
    managing_authority: str
    integration_source: str
    vendor: str
    model: str
    firmware_version: str
    protocol: str
    stream_url: str
    vms_system: Optional[str] = None
    vms_camera_ref: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude_m: Optional[float] = None
    direction_deg: Optional[int] = Field(None, ge=0, le=359)
    fov_h_deg: Optional[int] = None
    mount_height_m: Optional[float] = None
    location_type: str
    road: Optional[str] = None
    intersection: Optional[str] = None
    state: str = "Gujarat"
    district: str
    taluka: str
    police_station: str
    beat: Optional[str] = None
    jurisdiction_code: str
    resolution: str
    fps: int
    codec: str
    camera_type: CameraType
    status: CameraStatus = CameraStatus.ONLINE
    gateway_id: str
    edge_node_id: str
    retention_local_hrs: int
    retention_platform: int
    network_segment: str
    ip_address: str
    tags: List[str] = []

class CameraCreate(CameraBase):
    capabilities: CameraCapabilities

class CameraResponse(CameraBase):
    last_heartbeat: datetime
    uptime_30d_pct: float
    avg_bitrate_kbps: int
    onboarded_date: datetime
    last_maintenance: Optional[datetime] = None
    decommissioned: Optional[datetime] = None
    capabilities: CameraCapabilities
    
    model_config = ConfigDict(from_attributes=True)

class CameraHealthResponse(BaseModel):
    cam_id: str
    status: CameraStatus
    last_heartbeat: datetime
    uptime_30d_pct: float

class CameraListResponse(BaseModel):
    cameras: List[CameraResponse]
    total: int
