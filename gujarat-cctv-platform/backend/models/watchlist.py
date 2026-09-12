from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy import JSON, String
from datetime import datetime, timezone
import uuid
from typing import Optional, Any
from database import Base

class Watchlist(Base):
    __tablename__ = "watchlists"

    watchlist_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String)
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    entry_id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    watchlist_id: Mapped[Optional[str]] = mapped_column(ForeignKey("watchlists.watchlist_id", ondelete="CASCADE"))
    entity_type: Mapped[str] = mapped_column(String(50))
    identifier_value: Mapped[Optional[str]] = mapped_column(String(100))
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    added_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.user_id"))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
