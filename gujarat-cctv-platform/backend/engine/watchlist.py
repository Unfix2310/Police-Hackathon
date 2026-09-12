"""
Watchlist Matcher Module — v4.1

Checks resolved entities against active watchlist entries using
soft-biometric matching (color + vehicle class for vehicles,
clothing color for persons). When a match is found, creates an
Alert in the database and broadcasts it via WebSocket.

Matching strategy:
  - Vehicle: Check WatchlistEntry.entity_type == 'VEHICLE', compare
    identifier_value against plate (if readable), then compare
    attributes.color and attributes.vehicle_class against the entity.
  - Person: Check WatchlistEntry.entity_type == 'PERSON', compare
    attributes.clothing_color against the person entity.
"""

import logging
import uuid
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.watchlist import WatchlistEntry
from models.alert import Alert
from models.enums import AlertPriority

logger = logging.getLogger(__name__)


class WatchlistMatcher:
    """Matches entities against active watchlist entries and generates alerts."""

    def __init__(self):
        self._vehicle_entries: List[Dict[str, Any]] = []
        self._person_entries: List[Dict[str, Any]] = []
        self._loaded = False

    async def load_watchlist(self, db: AsyncSession) -> None:
        """Loads active watchlist entries into memory for fast checking."""
        try:
            stmt = select(WatchlistEntry).where(WatchlistEntry.status == "ACTIVE")
            result = await db.execute(stmt)
            entries = result.scalars().all()

            self._vehicle_entries = []
            self._person_entries = []

            for entry in entries:
                entry_dict = {
                    "entry_id": entry.entry_id,
                    "watchlist_id": entry.watchlist_id,
                    "entity_type": entry.entity_type,
                    "identifier_value": entry.identifier_value,
                    "attributes": entry.attributes or {},
                }
                if entry.entity_type == "VEHICLE":
                    self._vehicle_entries.append(entry_dict)
                elif entry.entity_type == "PERSON":
                    self._person_entries.append(entry_dict)

            self._loaded = True
            logger.info(f"Watchlist loaded: {len(self._vehicle_entries)} vehicles, {len(self._person_entries)} persons")

        except Exception as e:
            logger.warning(f"Could not load watchlist: {e}")

    async def check_vehicle(
        self,
        entity_id: str,
        plate: Optional[str],
        color: Optional[str],
        vehicle_class: Optional[str],
        camera_id: str,
        observation_id: str,
        timestamp: datetime,
        db: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """Check a resolved vehicle entity against the watchlist."""
        if not self._vehicle_entries:
            return None

        for entry in self._vehicle_entries:
            score = 0.0
            reasons = []

            # Plate match (if available and on watchlist)
            entry_plate = entry.get("identifier_value")
            if entry_plate and plate and plate not in ("UNREADABLE", "UNKNOWN"):
                norm_plate = re.sub(r"[^A-Z0-9]", "", str(plate).upper())
                norm_entry = re.sub(r"[^A-Z0-9]", "", str(entry_plate).upper())
                if norm_plate and norm_plate == norm_entry:
                    score += 0.5
                    reasons.append(f"plate={plate}")

            # Color match
            entry_color = entry["attributes"].get("color", "").lower()
            if entry_color and color and color.lower() == entry_color:
                score += 0.3
                reasons.append(f"color={color}")

            # Vehicle class match
            entry_class = entry["attributes"].get("vehicle_class", "").upper()
            if entry_class and vehicle_class and vehicle_class.upper() == entry_class:
                score += 0.2
                reasons.append(f"class={vehicle_class}")

            if score >= 0.5:
                alert = await self._create_alert(
                    alert_type="WATCHLIST_MATCH",
                    priority="P1" if score >= 0.8 else "P2",
                    message=f"Watchlist match: Entity {entity_id} at {camera_id}. Matched on: {', '.join(reasons)} (score={score:.2f})",
                    observation_id=observation_id,
                    timestamp=timestamp,
                    camera_id=camera_id,
                    entity_id=entity_id,
                    db=db,
                )
                return alert

        return None

    async def check_person(
        self,
        entity_id: str,
        clothing_color: Optional[str],
        camera_id: str,
        observation_id: str,
        timestamp: datetime,
        db: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """Check a resolved person entity against the watchlist."""
        if not self._person_entries:
            return None

        for entry in self._person_entries:
            entry_color = entry["attributes"].get("clothing_color", "").lower()

            if entry_color and clothing_color and clothing_color.lower() == entry_color:
                alert = await self._create_alert(
                    alert_type="WATCHLIST_MATCH",
                    priority="P3",
                    message=f"Person watchlist match: {entity_id} at {camera_id}. Clothing color: {clothing_color}",
                    observation_id=observation_id,
                    timestamp=timestamp,
                    camera_id=camera_id,
                    entity_id=entity_id,
                    db=db,
                )
                return alert

        return None

    async def _create_alert(
        self,
        alert_type: str,
        priority: str,
        message: str,
        observation_id: str,
        timestamp: datetime,
        camera_id: str,
        entity_id: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Create an Alert in DB and broadcast via WebSocket."""
        alert_id = f"ALT-{uuid.uuid4().hex[:10]}"

        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            priority=AlertPriority(priority),
            source_observation_id=observation_id,
            source_timestamp=timestamp,
            message=message,
            status="UNREAD",
            jurisdiction_code=None,
        )
        db.add(alert)

        alert_data = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "priority": priority,
            "message": message,
            "camera_id": camera_id,
            "entity_id": entity_id,
            "timestamp": timestamp.isoformat(),
            "status": "UNREAD",
        }

        # Broadcast via WebSocket (non-blocking, best-effort)
        try:
            from api.websocket import broadcast_alert
            import asyncio
            asyncio.create_task(broadcast_alert(alert_data))
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")

        logger.warning(f"🚨 ALERT {alert_id}: {message}")
        return alert_data


# ── Singleton ─────────────────────────────────────────────────────────────────

_matcher: Optional[WatchlistMatcher] = None

def get_watchlist_matcher() -> WatchlistMatcher:
    global _matcher
    if _matcher is None:
        _matcher = WatchlistMatcher()
    return _matcher
