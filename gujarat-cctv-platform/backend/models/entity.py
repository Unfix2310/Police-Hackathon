from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Optional, Any
from database import Base
from .enums import EntityStatus

class Person(Base):
    __tablename__ = "persons"

    person_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    running_confidence: Mapped[Optional[float]] = mapped_column(Float)
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[EntityStatus] = mapped_column(default=EntityStatus.CANDIDATE)

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    plate: Mapped[Optional[str]] = mapped_column(String(50))
    plate_confidence: Mapped[Optional[float]] = mapped_column(Float)
    color: Mapped[Optional[str]] = mapped_column(String(50))
    vehicle_class: Mapped[Optional[str]] = mapped_column(String(50))
    make_model: Mapped[Optional[str]] = mapped_column(String(100))
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[EntityStatus] = mapped_column(default=EntityStatus.ACTIVE)

class PersonObservation(Base):
    __tablename__ = "person_observations"

    person_id: Mapped[str] = mapped_column(ForeignKey("persons.person_id", ondelete="CASCADE"), primary_key=True)
    observation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    timestamp_capture: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float)

class VehicleObservation(Base):
    __tablename__ = "vehicle_observations"

    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), primary_key=True)
    observation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    timestamp_capture: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
