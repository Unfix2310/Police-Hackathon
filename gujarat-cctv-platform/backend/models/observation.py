from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, BIGINT
from datetime import datetime
from typing import Optional, Any
from database import Base
from .enums import ObservationType

class Observation(Base):
    __tablename__ = "observations"

    observation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    timestamp_capture: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    
    observation_type: Mapped[ObservationType] = mapped_column()
    source_camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.cam_id"))
    source_gateway_id: Mapped[Optional[str]] = mapped_column(String(100))
    source_edge_id: Mapped[Optional[str]] = mapped_column(String(100))
    timestamp_process: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    bounding_box: Mapped[Optional[list[int]]] = mapped_column(ARRAY(Integer))
    track_id: Mapped[Optional[str]] = mapped_column(String(100))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    
    feature_vector_ref: Mapped[Optional[str]] = mapped_column(String)
    frame_ref: Mapped[Optional[str]] = mapped_column(String)
    video_ref: Mapped[Optional[str]] = mapped_column(String)
    frame_offset_ms: Mapped[Optional[int]] = mapped_column(BIGINT)
    crop_ref: Mapped[Optional[str]] = mapped_column(String)
    
    model_id: Mapped[Optional[str]] = mapped_column(String(100))
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    model_hash: Mapped[Optional[str]] = mapped_column(String(100))
    processing_node: Mapped[Optional[str]] = mapped_column(String(100))
    processing_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    observation_hash: Mapped[Optional[str]] = mapped_column(String(100))
