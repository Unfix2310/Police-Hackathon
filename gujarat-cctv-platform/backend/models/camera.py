from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Date, DateTime, ARRAY, Boolean, ForeignKey
from datetime import datetime, date
from typing import Optional, List
from database import Base
from .enums import CameraStatus

class Camera(Base):
    __tablename__ = "cameras"

    cam_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    external_cam_id: Mapped[Optional[str]] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(String(200))
    owner_department: Mapped[Optional[str]] = mapped_column(String(100))
    managing_authority: Mapped[Optional[str]] = mapped_column(String(100))
    integration_source: Mapped[Optional[str]] = mapped_column(String(100))
    vendor: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))
    protocol: Mapped[Optional[str]] = mapped_column(String(50))
    stream_url: Mapped[Optional[str]] = mapped_column(String)
    vms_system: Mapped[Optional[str]] = mapped_column(String(100))
    vms_camera_ref: Mapped[Optional[str]] = mapped_column(String(100))
    
    # We omit PostGIS geometry for standard ORM usage if not using GeoAlchemy2,
    # or handle it as raw text/WKT. Using generic string/float for simplicity here.
    altitude_m: Mapped[Optional[float]] = mapped_column(Float)
    direction_deg: Mapped[Optional[int]] = mapped_column(Integer)
    fov_h_deg: Mapped[Optional[int]] = mapped_column(Integer)
    mount_height_m: Mapped[Optional[float]] = mapped_column(Float)
    location_type: Mapped[Optional[str]] = mapped_column(String(100))
    road: Mapped[Optional[str]] = mapped_column(String(150))
    intersection: Mapped[Optional[str]] = mapped_column(String(150))
    
    state: Mapped[str] = mapped_column(String(100), default="Gujarat")
    district: Mapped[Optional[str]] = mapped_column(String(100))
    taluka: Mapped[Optional[str]] = mapped_column(String(100))
    police_station: Mapped[Optional[str]] = mapped_column(String(100))
    beat: Mapped[Optional[str]] = mapped_column(String(100))
    jurisdiction_code: Mapped[str] = mapped_column(String(50))
    
    resolution: Mapped[Optional[str]] = mapped_column(String(50))
    fps: Mapped[Optional[int]] = mapped_column(Integer)
    codec: Mapped[Optional[str]] = mapped_column(String(50))
    camera_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    status: Mapped[CameraStatus] = mapped_column(default=CameraStatus.OFFLINE)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    uptime_30d_pct: Mapped[Optional[float]] = mapped_column(Float)
    avg_bitrate_kbps: Mapped[Optional[float]] = mapped_column(Float)
    
    gateway_id: Mapped[Optional[str]] = mapped_column(String(100))
    edge_node_id: Mapped[Optional[str]] = mapped_column(String(100))
    retention_local_hrs: Mapped[Optional[int]] = mapped_column(Integer)
    retention_platform: Mapped[Optional[str]] = mapped_column(String(100))
    
    onboarded_date: Mapped[Optional[date]] = mapped_column(Date)
    last_maintenance: Mapped[Optional[date]] = mapped_column(Date)
    decommissioned: Mapped[Optional[date]] = mapped_column(Date)
    network_segment: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))

class CameraCapability(Base):
    __tablename__ = "camera_capabilities"

    cam_id: Mapped[str] = mapped_column(ForeignKey("cameras.cam_id", ondelete="CASCADE"), primary_key=True)
    capability: Mapped[str] = mapped_column(String(100), primary_key=True)
    is_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    quality: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(String)
