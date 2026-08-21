from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime
from datetime import datetime, timezone
from typing import Optional
from database import Base
from .enums import IncidentSeverity

class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[IncidentSeverity] = mapped_column()
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    description: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    jurisdiction_code: Mapped[str] = mapped_column(String(50))
