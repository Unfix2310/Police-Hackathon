from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy import String
from datetime import datetime, timezone
from typing import Optional
from database import Base

class EvidencePackage(Base):
    __tablename__ = "evidence_packages"

    package_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    case_reference: Mapped[Optional[str]] = mapped_column(ForeignKey("cases.case_id"))
    fir_reference: Mapped[Optional[str]] = mapped_column(String(100))
    generated_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.user_id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    package_hash: Mapped[Optional[str]] = mapped_column(String(100))
    purpose: Mapped[Optional[str]] = mapped_column(String)

class EvidenceObservation(Base):
    __tablename__ = "evidence_observations"

    package_id: Mapped[str] = mapped_column(ForeignKey("evidence_packages.package_id", ondelete="CASCADE"), primary_key=True)
    observation_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp_capture: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
