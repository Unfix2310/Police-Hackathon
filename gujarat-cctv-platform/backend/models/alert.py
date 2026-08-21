from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
from typing import Optional
from database import Base
from .enums import AlertPriority

class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[str] = mapped_column(String(100))
    priority: Mapped[AlertPriority] = mapped_column()
    source_observation_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True))
    source_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    message: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default="UNREAD")
    jurisdiction_code: Mapped[Optional[str]] = mapped_column(String(50))
