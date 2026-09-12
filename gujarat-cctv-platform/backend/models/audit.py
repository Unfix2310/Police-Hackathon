from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy import JSON, String
from datetime import datetime, timezone
import uuid
from typing import Optional, Any
from database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(50))
    role: Mapped[Optional[str]] = mapped_column(String(50))
    case_id: Mapped[Optional[str]] = mapped_column(String(50))
    purpose: Mapped[Optional[str]] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    query_type: Mapped[str] = mapped_column(String(100))
    query_params: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    result_count: Mapped[Optional[int]] = mapped_column(Integer)
    data_accessed: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    export: Mapped[bool] = mapped_column(Boolean, default=False)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45))
