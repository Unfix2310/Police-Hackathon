from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Date, ForeignKey, JSON
from datetime import datetime, date, timezone
from typing import Optional
from database import Base
from .enums import CaseStatus

class Case(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    fir_reference: Mapped[Optional[str]] = mapped_column(String(100))
    cctns_case_ref: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    police_station: Mapped[Optional[str]] = mapped_column(String(100))
    jurisdiction_code: Mapped[str] = mapped_column(String(50))
    investigating_officer: Mapped[Optional[str]] = mapped_column(ForeignKey("users.user_id"))
    supervising_officer: Mapped[Optional[str]] = mapped_column(ForeignKey("users.user_id"))
    assigned_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[CaseStatus] = mapped_column(default=CaseStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    access_list: Mapped[Optional[list[str]]] = mapped_column(JSON)
    access_justification: Mapped[Optional[str]] = mapped_column(String)
    classification: Mapped[Optional[str]] = mapped_column(String(50))

class CaseEntity(Base):
    __tablename__ = "case_entities" # Link table for generalized case links if needed

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id", ondelete="CASCADE"), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), primary_key=True) # PERSON, VEHICLE, INCIDENT
