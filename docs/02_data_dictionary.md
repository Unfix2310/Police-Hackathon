# Data Dictionary & Models

This document defines the canonical data models for the Gujarat CCTV Intelligence Platform. These models are defined using Pydantic, enabling direct use in the FastAPI backend, automatic OpenAPI schema generation, and robust validation.

## 1. Enumerations

```python
from enum import Enum

class ObservationType(str, Enum):
    PERSON = "PERSON"
    VEHICLE = "VEHICLE"
    OBJECT = "OBJECT"
    EVENT = "EVENT"

class EntityStatus(str, Enum):
    DETECTED = "DETECTED"
    OBSERVED = "OBSERVED"
    ASSOCIATED = "ASSOCIATED"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    CONFIRMED = "CONFIRMED"

class CameraStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"

class IncidentSeverity(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"

class CaseStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    CHARGE_SHEET = "CHARGE_SHEET"
    CLOSED = "CLOSED"

class AlertType(str, Enum):
    WATCHLIST_MATCH = "WATCHLIST_MATCH"
    ZONE_INTRUSION = "ZONE_INTRUSION"
    ANOMALY = "ANOMALY"
    CAMERA_HEALTH = "CAMERA_HEALTH"
    SYSTEM = "SYSTEM"

class FeasibilityLabel(str, Enum):
    PLAUSIBLE = "PLAUSIBLE"
    POSSIBLE = "POSSIBLE"
    LOW_PLAUSIBILITY = "LOW_PLAUSIBILITY"
    IMPLAUSIBLE = "IMPLAUSIBLE"
    PHYSICALLY_IMPOSSIBLE = "PHYSICALLY_IMPOSSIBLE"

class UserRole(str, Enum):
    OPERATOR = "OPERATOR"
    INVESTIGATOR = "INVESTIGATOR"
    COMMAND = "COMMAND"
    FIELD_OFFICER = "FIELD_OFFICER"
    ADMIN = "ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    AUDITOR = "AUDITOR"

class VehicleClass(str, Enum):
    SEDAN = "SEDAN"
    SUV = "SUV"
    HATCHBACK = "HATCHBACK"
    TWO_WHEELER = "TWO_WHEELER"
    AUTO_RICKSHAW = "AUTO_RICKSHAW"
    BUS = "BUS"
    TRUCK = "TRUCK"
    TRACTOR = "TRACTOR"
    BULLOCK_CART = "BULLOCK_CART"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class CameraType(str, Enum):
    FIXED = "FIXED"
    PTZ = "PTZ"
    DOME = "DOME"
    BULLET = "BULLET"
    OTHER = "OTHER"

class CapabilityQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"
```

## 2. Infrastructure & Perception Models

```python
from pydantic import BaseModel, Field, constr
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class CameraCapabilities(BaseModel):
    anpr: CapabilityQuality = Field(..., description="ANPR capability quality")
    ptz: bool = Field(False, description="Whether camera has Pan-Tilt-Zoom capabilities")
    audio: bool = Field(False, description="Audio capture capability")
    person_detection: CapabilityQuality = Field(..., description="Person detection quality")
    vehicle_detection: CapabilityQuality = Field(..., description="Vehicle detection quality")
    night_vision: CapabilityQuality = Field(..., description="Night vision / IR capability")
    crowd_estimation: CapabilityQuality = Field(..., description="Crowd estimation suitability")
    speed_estimation: bool = Field(False, description="Can estimate speed (calibrated)")
    direction_detection: CapabilityQuality = Field(..., description="Can detect movement direction")

class CameraRecord(BaseModel):
    cam_id: str = Field(..., description="Platform-assigned immutable ID (e.g., CAM-GJ-AHM-SG-0142)", pattern=r"^CAM-[A-Z]{2}-[A-Z]{3}-.+$")
    external_cam_id: Optional[str] = Field(None, description="VMS-specific or NVR-specific reference")
    display_name: str = Field(..., description="Human-readable name")
    owner_department: str = Field(..., description="Owner (e.g., Gujarat Police, AMC, NHAI)")
    managing_authority: str = Field(..., description="Authority managing the camera")
    integration_source: str = Field(..., description="Source system (e.g., Milestone VMS, Direct RTSP)")
    vendor: str = Field(..., description="Camera vendor")
    model: str = Field(..., description="Camera model")
    firmware_version: str = Field(..., description="Firmware version")
    protocol: str = Field(..., description="Stream protocol (e.g., RTSP, ONVIF)")
    stream_url: str = Field(..., description="Internal stream URL via integration fabric")
    vms_system: Optional[str] = Field(None, description="VMS System if applicable")
    vms_camera_ref: Optional[str] = Field(None, description="Internal VMS reference")
    
    # Location
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    altitude_m: Optional[float] = Field(None, description="Altitude in meters")
    direction_deg: Optional[int] = Field(None, ge=0, le=359, description="Compass bearing of FOV center")
    fov_h_deg: Optional[int] = Field(None, description="Horizontal Field of View in degrees")
    mount_height_m: Optional[float] = Field(None, description="Mounting height in meters")
    location_type: str = Field(..., description="Location category (intersection, highway, etc.)")
    road: Optional[str] = Field(None, description="Road name")
    intersection: Optional[str] = Field(None, description="Intersection name if applicable")
    
    # Jurisdiction
    state: str = Field("Gujarat", description="State")
    district: str = Field(..., description="District name")
    taluka: str = Field(..., description="Taluka name")
    police_station: str = Field(..., description="Police station name")
    beat: Optional[str] = Field(None, description="Beat name/number")
    jurisdiction_code: str = Field(..., description="Standard jurisdiction code (e.g., GJ-AHM-SAT)")
    
    # Technical
    resolution: str = Field(..., description="Resolution (e.g., 2560x1440)")
    fps: int = Field(..., description="Frames per second")
    codec: str = Field(..., description="Video codec (e.g., H.265)")
    camera_type: CameraType = Field(..., description="Type of camera")
    
    # Status
    status: CameraStatus = Field(default=CameraStatus.ONLINE, description="Current operational status")
    last_heartbeat: datetime = Field(..., description="Last received heartbeat timestamp")
    uptime_30d_pct: float = Field(..., ge=0, le=100, description="30-day uptime percentage")
    avg_bitrate_kbps: int = Field(..., description="Average bitrate in kbps")
    
    # Edge mapping
    gateway_id: str = Field(..., description="Gateway node ID")
    edge_node_id: str = Field(..., description="Processing edge node ID")
    
    # Management
    retention_local_hrs: int = Field(..., description="Retention at local edge/NVR in hours")
    retention_platform: int = Field(..., description="Retention on platform in hours")
    onboarded_date: datetime = Field(..., description="Date added to platform")
    last_maintenance: Optional[datetime] = Field(None, description="Last maintenance date")
    decommissioned: Optional[datetime] = Field(None, description="Decommission date if inactive")
    network_segment: str = Field(..., description="Network segment identifier")
    ip_address: str = Field(..., description="Internal IP address")
    tags: List[str] = Field(default_factory=list, description="Tags like 'highway', 'anpr_suitable'")
    
    capabilities: CameraCapabilities = Field(..., description="Camera AI capabilities")
```

## 3. Observation Models

```python
class ObservationPayloadPerson(BaseModel):
    clothing: str = Field(..., description="Description of clothing (e.g., 'blue shirt, dark pants')")
    bag: Optional[str] = Field(None, description="Bag description (e.g., 'backpack')")
    helmet: bool = Field(False, description="Whether wearing a helmet")
    gender_estimate: Optional[str] = Field(None, description="Estimated gender (e.g., 'male')")

class ObservationPayloadVehicle(BaseModel):
    plate: Optional[str] = Field(None, description="License plate text", pattern=r"^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$")
    plate_confidence: Optional[float] = Field(None, ge=0, le=1.0, description="OCR confidence")
    color: Optional[str] = Field(None, description="Vehicle color")
    vehicle_class: VehicleClass = Field(default=VehicleClass.UNKNOWN, description="Vehicle classification")
    make_model: Optional[str] = Field(None, description="Make and model estimate")

class ObservationPayloadEvent(BaseModel):
    event_type: str = Field(..., description="Event type (e.g., 'ZONE_INTRUSION')")
    severity: IncidentSeverity = Field(..., description="Event severity")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event specific details")

class Observation(BaseModel):
    observation_id: UUID = Field(..., description="Globally unique immutable ID")
    observation_type: ObservationType = Field(..., description="Type of observation")
    
    source_camera_id: str = Field(..., description="ID of source camera")
    source_gateway_id: str = Field(..., description="ID of source gateway")
    source_edge_id: str = Field(..., description="ID of processing edge node")
    
    timestamp_capture: datetime = Field(..., description="Camera-synced NTP capture time")
    timestamp_process: datetime = Field(..., description="Processing completion time")
    
    location_lat: float = Field(..., ge=-90, le=90, description="Latitude at time of observation")
    location_lng: float = Field(..., ge=-180, le=180, description="Longitude at time of observation")
    
    bounding_box: List[int] = Field(..., min_length=4, max_length=4, description="[x1, y1, x2, y2] pixel coordinates")
    track_id: str = Field(..., description="Within-camera track ID")
    confidence: float = Field(..., ge=0, le=1.0, description="Detection confidence")
    
    payload: Dict[str, Any] = Field(..., description="Type-specific payload (Person/Vehicle/Event)")
    
    feature_vector_ref: Optional[str] = Field(None, description="URI reference to feature vector store")
    frame_ref: str = Field(..., description="URI to original frame in object store")
    video_ref: str = Field(..., description="URI to video segment in object store")
    frame_offset_ms: int = Field(..., description="Offset in milliseconds into the video segment")
    crop_ref: Optional[str] = Field(None, description="URI to cropped image of detection")
    
    model_id: str = Field(..., description="AI Model used for detection")
    model_version: str = Field(..., description="Version of the model")
    model_hash: str = Field(..., description="SHA-256 hash of the model")
    processing_node: str = Field(..., description="Node where processing occurred")
    processing_latency: int = Field(..., description="Processing latency in milliseconds")
    
    observation_hash: str = Field(..., description="SHA-256 integrity hash of this record")
```

## 4. Entity Models

```python
class PersonEntity(BaseModel):
    person_id: str = Field(..., description="System generated entity ID (e.g., P-7834)", pattern=r"^P-\d+$")
    first_seen: datetime = Field(..., description="Timestamp of first observation")
    last_seen: datetime = Field(..., description="Timestamp of last observation")
    observation_count: int = Field(..., ge=1, description="Number of observations associated")
    observation_ids: List[UUID] = Field(..., description="List of observation UUIDs")
    running_confidence: float = Field(..., ge=0, le=1.0, description="Overall confidence of this entity grouping")
    attributes: ObservationPayloadPerson = Field(..., description="Aggregated person attributes")
    watchlist_matches: List[str] = Field(default_factory=list, description="IDs of matching watchlist entries")
    status: EntityStatus = Field(..., description="Association status of this entity")

class VehicleEntity(BaseModel):
    vehicle_id: str = Field(..., description="System generated entity ID (e.g., V-4521)", pattern=r"^V-\d+$")
    plate: Optional[str] = Field(None, description="Best plate read")
    plate_confidence: Optional[float] = Field(None, ge=0, le=1.0, description="Confidence of the best plate read")
    color: Optional[str] = Field(None, description="Dominant color")
    vehicle_class: VehicleClass = Field(default=VehicleClass.UNKNOWN, description="Vehicle class")
    make_model: Optional[str] = Field(None, description="Make and model")
    first_seen: datetime = Field(..., description="Timestamp of first observation")
    last_seen: datetime = Field(..., description="Timestamp of last observation")
    observation_count: int = Field(..., ge=1, description="Number of observations associated")
    observation_ids: List[UUID] = Field(..., description="List of observation UUIDs")
    associated_persons: List[str] = Field(default_factory=list, description="List of person_ids associated with this vehicle")
    watchlist_matches: List[str] = Field(default_factory=list, description="IDs of matching watchlist entries")
    status: EntityStatus = Field(..., description="Association status of this entity")
```

## 5. Case & Investigation Models

```python
class Incident(BaseModel):
    incident_id: str = Field(..., description="Incident ID (e.g., I-4521)", pattern=r"^I-\d+$")
    type: str = Field(..., description="Type of incident")
    severity: IncidentSeverity = Field(..., description="Priority/Severity")
    location_lat: float = Field(..., description="Incident latitude")
    location_lng: float = Field(..., description="Incident longitude")
    start_time: datetime = Field(..., description="Incident start time")
    end_time: Optional[datetime] = Field(None, description="Incident end/resolution time")
    observations: List[UUID] = Field(default_factory=list, description="Correlated observations")
    description: str = Field(..., description="Incident description")
    status: str = Field(..., description="Incident status (e.g., VERIFIED, DISPATCHED, RESOLVED)")

class TimelineEntry(BaseModel):
    timestamp: datetime = Field(..., description="Event time")
    camera_id: str = Field(..., description="Camera involved")
    location_name: str = Field(..., description="Human readable location")
    confidence: float = Field(..., description="Confidence score")
    type: str = Field(..., description="Type (e.g., ANPR, Person Detection)")
    description: str = Field(..., description="Event description")
    observations: List[UUID] = Field(default_factory=list, description="Related observations")

class EvidencePackage(BaseModel):
    package_id: str = Field(..., description="Evidence package ID (e.g., EP-2026-4521-001)")
    case_reference: str = Field(..., description="Internal case ID")
    fir_reference: Optional[str] = Field(None, description="CCTNS FIR Reference")
    generated_by: str = Field(..., description="Officer generating the package")
    generated_at: datetime = Field(..., description="Generation timestamp")
    package_hash: str = Field(..., description="SHA-256 hash of entire package contents")
    purpose: str = Field(..., description="Purpose of evidence (e.g., 'Vehicle trajectory evidence')")
    timeline: List[TimelineEntry] = Field(..., description="Event timeline")
    trajectory_validation: Dict[str, Any] = Field(..., description="Spatio-temporal validation results")
    associated_persons: List[str] = Field(default_factory=list, description="Related person IDs")
    video_clips: List[Dict[str, str]] = Field(..., description="List of video clips with their hashes")
    metadata: Dict[str, Any] = Field(..., description="Additional evidentiary metadata (e.g., Sec 65B info)")

class Case(BaseModel):
    case_id: str = Field(..., description="Case ID (e.g., CASE-2026-AHM-SAT-0421)")
    fir_reference: Optional[str] = Field(None, description="CCTNS FIR Reference")
    cctns_case_ref: Optional[str] = Field(None, description="CCTNS system ID")
    district: str = Field(..., description="District")
    police_station: str = Field(..., description="Police Station")
    jurisdiction_code: str = Field(..., description="Jurisdiction Code")
    investigating_officer: str = Field(..., description="IO Name and Badge")
    supervising_officer: str = Field(..., description="Supervising Officer Name")
    assigned_date: datetime = Field(..., description="Assignment date")
    incidents: List[str] = Field(default_factory=list, description="Linked incident IDs")
    persons: List[str] = Field(default_factory=list, description="Linked person IDs")
    vehicles: List[str] = Field(default_factory=list, description="Linked vehicle IDs")
    observations: List[UUID] = Field(default_factory=list, description="Linked observation UUIDs")
    cameras: List[str] = Field(default_factory=list, description="Linked camera IDs")
    timeline: List[TimelineEntry] = Field(default_factory=list, description="Manual or auto-generated case timeline")
    evidence_packages: List[str] = Field(default_factory=list, description="Linked evidence package IDs")
    investigator_notes: List[Dict[str, Any]] = Field(default_factory=list, description="Structured notes")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Action log")
    access_list: List[str] = Field(..., description="List of users authorized to view case")
    access_justification: str = Field(..., description="Justification for case creation/access")
    classification: str = Field(default="RESTRICTED", description="Security classification")
    status: CaseStatus = Field(default=CaseStatus.OPEN, description="Case status")
    created: datetime = Field(..., description="Case creation time")
    last_updated: datetime = Field(..., description="Last update time")
    audit_trail: List[str] = Field(default_factory=list, description="Links to audit logs")
```

## 6. Correlation & Search Models

```python
class TrajectoryPoint(BaseModel):
    location_lat: float = Field(..., description="Point latitude")
    location_lng: float = Field(..., description="Point longitude")
    timestamp: datetime = Field(..., description="Timestamp at point")
    camera_id: str = Field(..., description="Camera ID at point")

class FeasibilityResult(BaseModel):
    score: float = Field(..., ge=0, le=1.0, description="Feasibility score")
    label: FeasibilityLabel = Field(..., description="Feasibility classification label")
    required_speed_kmh: float = Field(..., description="Calculated required speed in km/h")
    road_distance_km: float = Field(..., description="Road network distance in km")
    road_class: str = Field(..., description="Type of road (e.g., highway, city)")
    explanation: str = Field(..., description="Human readable explanation")

class TrajectoryResult(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle entity ID")
    points: List[TrajectoryPoint] = Field(..., description="List of trajectory points")
    distances: List[float] = Field(..., description="Distances between points in km")
    average_speed: float = Field(..., description="Average speed across trajectory")
    feasibility_score: float = Field(..., ge=0, le=1.0, description="Overall feasibility score")
    feasibility_label: FeasibilityLabel = Field(..., description="Overall feasibility label")
```

## 7. Operations & Security Models

```python
class WatchlistEntry(BaseModel):
    entry_id: str = Field(..., description="Watchlist entry ID")
    type: ObservationType = Field(..., description="Type of entity (PERSON/VEHICLE)")
    entity_id: str = Field(..., description="Plate number or Feature Reference")
    reason: str = Field(..., description="Reason for watchlisting")
    priority: IncidentSeverity = Field(..., description="Priority if matched")
    added_by: str = Field(..., description="User ID who added entry")
    added_at: datetime = Field(..., description="Timestamp of addition")
    expiry: Optional[datetime] = Field(None, description="Expiry date of entry")

class Alert(BaseModel):
    alert_id: str = Field(..., description="Alert ID")
    type: AlertType = Field(..., description="Alert category")
    priority: IncidentSeverity = Field(..., description="Alert priority")
    timestamp: datetime = Field(..., description="Alert generation time")
    location_lat: Optional[float] = Field(None, description="Latitude if applicable")
    location_lng: Optional[float] = Field(None, description="Longitude if applicable")
    description: str = Field(..., description="Alert details")
    linked_observation_id: Optional[UUID] = Field(None, description="Triggering observation")
    status: str = Field(default="NEW", description="Alert status (NEW, ACKNOWLEDGED, RESOLVED)")

class UserProfile(BaseModel):
    user_id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User Role")
    name: str = Field(..., description="Full Name")
    badge_id: Optional[str] = Field(None, description="Police Badge ID")
    district: str = Field(..., description="Assigned district")
    police_station: Optional[str] = Field(None, description="Assigned Police Station")
    email: str = Field(..., description="Official Email")

class AuditLogEntry(BaseModel):
    log_id: UUID = Field(..., description="Log UUID")
    timestamp: datetime = Field(..., description="Action timestamp")
    user_id: str = Field(..., description="User ID performing action")
    action: str = Field(..., description="Action taken (e.g., VIEW_CASE, EXPORT_EVIDENCE)")
    resource_type: str = Field(..., description="Type of resource accessed")
    resource_id: str = Field(..., description="ID of resource accessed")
    case_id: Optional[str] = Field(None, description="Case ID providing justification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
```

## 8. Relationship Diagram (Text-Based)

```
[CameraRecord] 1 ----- * [Observation]
                             |
                             | (captured by)
                             v
                       [CameraRecord]
                             
[Observation] * ------ 1 [PersonEntity]  (grouped into)
[Observation] * ------ 1 [VehicleEntity] (grouped into)

[Observation] * ------ * [Incident] (part of)
[Incident] * --------- 1 [Case] (related to)

[Observation] * ------ 1 [EvidencePackage] (supported by)
[EvidencePackage] * -- 1 [Case] (generated for)

[PersonEntity] * ----- * [VehicleEntity] (associated with)

[PersonEntity] * ----- 1 [WatchlistEntry] (matches)
[VehicleEntity] * ---- 1 [WatchlistEntry] (matches)

[Observation] 1 ------ 1 [Alert] (triggers)
```

## 9. JSON Data Examples (Realistic Gujarat Data)

### Vehicle Observation Example
```json
{
  "observation_id": "123e4567-e89b-12d3-a456-426614174000",
  "observation_type": "VEHICLE",
  "source_camera_id": "CAM-GJ-AHM-SG-0142",
  "source_gateway_id": "GW-AHM-WEST-02",
  "source_edge_id": "EDGE-AHM-SAT-01",
  "timestamp_capture": "2026-08-19T18:32:14.237+05:30",
  "timestamp_process": "2026-08-19T18:32:14.891+05:30",
  "location_lat": 23.0395,
  "location_lng": 72.5268,
  "bounding_box": [120, 340, 450, 680],
  "track_id": "T-142",
  "confidence": 0.94,
  "payload": {
    "plate": "GJ01AB1234",
    "plate_confidence": 0.96,
    "color": "White",
    "vehicle_class": "SEDAN",
    "make_model": "Maruti Dzire"
  },
  "feature_vector_ref": "vectordb://vehicle-features/obs-123e...",
  "frame_ref": "s3://frames/2026/08/19/CAM-GJ-AHM-SG-0142/18-32-14-237.jpg",
  "video_ref": "s3://video/2026/08/19/CAM-GJ-AHM-SG-0142/18-30-00.mp4",
  "frame_offset_ms": 134237,
  "crop_ref": "s3://crops/2026/08/19/obs-123e....jpg",
  "model_id": "vehicle-detect-anpr-v4.1",
  "model_version": "4.1.0",
  "model_hash": "sha256:a1b2c3...",
  "processing_node": "edge-ahm-sat-01",
  "processing_latency": 47,
  "observation_hash": "sha256:d4e5f6..."
}
```

### Case Example
```json
{
  "case_id": "CASE-2026-AHM-SAT-0421",
  "fir_reference": "FIR/AHM/SAT/2026/4521",
  "cctns_case_ref": "CCTNS-99812",
  "district": "Ahmedabad",
  "police_station": "Satellite PS",
  "jurisdiction_code": "GJ-AHM-SAT",
  "investigating_officer": "PI R.K. Sharma (Badge: GJ-PI-4421)",
  "supervising_officer": "DySP M.N. Patel",
  "assigned_date": "2026-08-19T20:00:00+05:30",
  "incidents": ["I-4521"],
  "persons": ["P-17", "P-22"],
  "vehicles": ["V-4521"],
  "observations": ["123e4567-e89b-12d3-a456-426614174000"],
  "cameras": ["CAM-GJ-AHM-SG-0101", "CAM-GJ-AHM-SG-0113"],
  "timeline": [],
  "evidence_packages": ["EP-2026-4521-001"],
  "investigator_notes": [
    {
      "timestamp": "2026-08-19T21:00:00+05:30",
      "author": "PI R.K. Sharma",
      "note": "Vehicle V-4521 tracked successfully from ISRO to Motera. Suspect identified as P-22 based on physical attributes and trajectory."
    }
  ],
  "actions": [],
  "access_list": ["GJ-PI-4421", "GJ-DYSP-8812"],
  "access_justification": "Investigation for FIR/AHM/SAT/2026/4521",
  "classification": "RESTRICTED",
  "status": "UNDER_INVESTIGATION",
  "created": "2026-08-19T20:00:00+05:30",
  "last_updated": "2026-08-19T22:15:00+05:30",
  "audit_trail": ["audit-log-uuid-1", "audit-log-uuid-2"]
}
```
