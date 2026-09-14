"""
Entity Resolver Module — Soft-Biometric Corridor Tracking (v4.1)

Resolves raw observations into persistent Vehicle and Person entities using
visual profile matching (Color + Class + Spatio-Temporal Feasibility) instead
of relying on license plate OCR, which is physically unreadable on wide-angle
junction CCTV cameras.

Resolution strategy:
  1. VEHICLE: Match by (vehicle_class + color) on the same or adjacent camera
     within a configurable time window. Compute a weighted score:
       Score = 0.40 * ClassMatch + 0.35 * ColorMatch + 0.25 * TemporalProximity
     If Score >= 0.70 → link to existing entity.
     Otherwise → create new entity with an operational token (V-{CAM}-{HEX}).

  2. PERSON: Match by clothing color on the same camera within a short window.
     Deep ReID features are not viable with the current 16x32 grayscale extractor,
     so we use a simpler same-camera temporal association.
"""

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.entity import Vehicle, Person, VehicleObservation, PersonObservation
from models.observation import Observation
from config import settings

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

VEHICLE_MATCH_WINDOW_SEC = 600       # 10 minutes: look for same vehicle within this window
PERSON_MATCH_WINDOW_SEC = 600        # 10 minutes: look for same person within this window
VEHICLE_MATCH_THRESHOLD = 0.70       # Minimum score to link to existing entity
PERSON_MATCH_THRESHOLD = 0.60        # Minimum score to link to existing person

# Weights for soft-biometric vehicle matching
W_CLASS = 0.40
W_COLOR = 0.35
W_TEMPORAL = 0.25


# ── Helpers ───────────────────────────────────────────────────────────────────

def _color_similarity(c1: Optional[str], c2: Optional[str]) -> float:
    """Returns 1.0 for exact match, 0.5 for close-family match, 0.0 otherwise."""
    if not c1 or not c2:
        return 0.0
    c1, c2 = c1.lower().strip(), c2.lower().strip()
    if c1 == c2:
        return 1.0
    # Close-family groups
    families = [
        {"white", "silver", "grey"},
        {"black", "grey"},
        {"red", "maroon"},
        {"blue", "navy"},
        {"yellow", "green"},   # auto-rickshaw family
    ]
    for fam in families:
        if c1 in fam and c2 in fam:
            return 0.5
    return 0.0


def _class_similarity(c1: Optional[str], c2: Optional[str]) -> float:
    """Returns 1.0 for exact match, 0.3 for broad-family match, 0.0 otherwise."""
    if not c1 or not c2:
        return 0.0
    c1, c2 = c1.upper().strip(), c2.upper().strip()
    if c1 == c2:
        return 1.0
    # Broad families
    families = [
        {"SEDAN", "SUV", "HATCHBACK", "VAN", "CAR"},
        {"BUS", "MINIBUS"},
        {"TRUCK", "LORRY", "HEAVY"},
        {"TWO_WHEELER", "MOTORCYCLE", "SCOOTER"},
        {"AUTO_RICKSHAW", "AUTO"},
    ]
    for fam in families:
        if c1 in fam and c2 in fam:
            return 0.3
    return 0.0


def _diff_seconds(t1: datetime, t2: datetime) -> float:
    """Returns (t2 - t1) in seconds, normalizing timezone awareness."""
    if t1.tzinfo is not None and t2.tzinfo is None:
        t2 = t2.replace(tzinfo=t1.tzinfo)
    elif t1.tzinfo is None and t2.tzinfo is not None:
        t1 = t1.replace(tzinfo=t2.tzinfo)
    return (t2 - t1).total_seconds()


def _temporal_proximity(t1: datetime, t2: datetime, window_sec: float) -> float:
    """Returns 1.0 when times are very close, decaying to 0.0 at the window edge."""
    delta = abs(_diff_seconds(t1, t2))
    if delta >= window_sec:
        return 0.0
    return 1.0 - (delta / window_sec)


# ── Main Resolver ─────────────────────────────────────────────────────────────

class EntityResolver:
    """
    Resolves raw observations into persistent Vehicle / Person entities
    using soft-biometric corridor tracking.
    """

    async def resolve_vehicle(
        self,
        obs_id: str,
        timestamp: datetime,
        camera_id: str,
        color: Optional[str],
        vehicle_class: Optional[str],
        plate: Optional[str],
        plate_confidence: float,
        confidence: float,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Resolve a vehicle observation to a persistent entity.
        Returns {"entity_id": str, "confidence": float, "method": str, "is_new": bool}.
        """
        # ── Step 1: Try exact plate match if plate was readable ────────────
        if plate and plate not in ("UNREADABLE", "UNREADABLE_LOW_RES", "UNKNOWN", None) and plate_confidence > 0.7:
            stmt = select(Vehicle).where(Vehicle.plate == plate).limit(1)
            result = await db.execute(stmt)
            match = result.scalar_one_or_none()
            if match:
                await self._update_vehicle(match, timestamp, confidence, db)
                await self._link_vehicle_obs(match.vehicle_id, obs_id, timestamp, confidence, db)
                return {"entity_id": match.vehicle_id, "confidence": 0.95, "method": "EXACT_PLATE", "is_new": False}

        # ── Step 2: Soft-biometric corridor matching ──────────────────────
        window_start = timestamp - timedelta(seconds=VEHICLE_MATCH_WINDOW_SEC)

        # Find recent vehicles seen on the same camera or any camera within window
        stmt = (
            select(Vehicle, VehicleObservation)
            .join(VehicleObservation, Vehicle.vehicle_id == VehicleObservation.vehicle_id)
            .where(VehicleObservation.timestamp_capture >= window_start)
            .where(VehicleObservation.timestamp_capture <= timestamp)
            .order_by(VehicleObservation.timestamp_capture.desc())
            .limit(50)
        )
        result = await db.execute(stmt)
        candidates = result.all()

        best_score = 0.0
        best_match: Optional[Vehicle] = None

        for veh, veh_obs in candidates:
            # ── Spatial feasibility gate ──────────────────────────
            # Skip if the vehicle was last seen on a camera too far away
            # to have physically traveled in the elapsed time
            if veh_obs.observation_id:  # has a linked observation
                try:
                    from simulator.camera_registry import get_camera
                    import math
                    last_cam_id = None
                    # Get the camera from the linked observation
                    obs_result = await db.execute(
                        select(Observation.source_camera_id)
                        .where(Observation.observation_id == veh_obs.observation_id)
                        .limit(1)
                    )
                    row = obs_result.scalar_one_or_none()
                    if row:
                        last_cam_id = row
                    
                    if last_cam_id and last_cam_id != camera_id:
                        cam_a = get_camera(camera_id)
                        cam_b = get_camera(last_cam_id)
                        if cam_a and cam_b:
                            lat1 = cam_a.get("latitude") or cam_a.get("lat", 0)
                            lng1 = cam_a.get("longitude") or cam_a.get("lng", 0)
                            lat2 = cam_b.get("latitude") or cam_b.get("lat", 0)
                            lng2 = cam_b.get("longitude") or cam_b.get("lng", 0)
                            if lat1 and lng1 and lat2 and lng2:
                                # Haversine distance in km
                                dlat = math.radians(lat2 - lat1)
                                dlng = math.radians(lng2 - lng1)
                                a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
                                dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                                
                                elapsed_hrs = _diff_seconds(veh_obs.timestamp_capture, timestamp) / 3600.0
                                if elapsed_hrs > 0:
                                    implied_speed = dist_km / elapsed_hrs
                                    if implied_speed > settings.PHYSICAL_MAX_VEHICLE_SPEED_KMH:  # km/h max plausible speed
                                        continue  # Skip: physically impossible travel
                except Exception:
                    pass  # If lookup fails, proceed with matching

            cls_score = _class_similarity(vehicle_class, veh.vehicle_class)
            col_score = _color_similarity(color, veh.color)
            tmp_score = _temporal_proximity(veh_obs.timestamp_capture, timestamp, VEHICLE_MATCH_WINDOW_SEC)

            score = (W_CLASS * cls_score) + (W_COLOR * col_score) + (W_TEMPORAL * tmp_score)

            if score > best_score:
                best_score = score
                best_match = veh

        if best_match and best_score >= VEHICLE_MATCH_THRESHOLD:
            await self._update_vehicle(best_match, timestamp, confidence, db)
            await self._link_vehicle_obs(best_match.vehicle_id, obs_id, timestamp, confidence, db)
            return {
                "entity_id": best_match.vehicle_id,
                "confidence": round(best_score, 3),
                "method": "SOFT_BIOMETRIC",
                "is_new": False,
            }

        # ── Step 3: Create new vehicle entity ─────────────────────────────
        cam_short = camera_id.replace("cam", "").replace("CAM-", "")[:4]
        color_tag = (color or "UNK")[:3].upper()
        new_id = f"V-{cam_short}-{color_tag}-{uuid.uuid4().hex[:6]}"

        new_vehicle = Vehicle(
            vehicle_id=new_id,
            plate=plate if plate and plate not in ("UNREADABLE", "UNREADABLE_LOW_RES", "UNKNOWN") else None,
            plate_confidence=plate_confidence if plate_confidence > 0.1 else None,
            color=color,
            vehicle_class=vehicle_class or "UNKNOWN",
            first_seen=timestamp,
            last_seen=timestamp,
            observation_count=1,
        )
        db.add(new_vehicle)
        await self._link_vehicle_obs(new_id, obs_id, timestamp, confidence, db)

        return {"entity_id": new_id, "confidence": 0.50, "method": "NEW_ENTITY", "is_new": True}

    async def resolve_person(
        self,
        obs_id: str,
        timestamp: datetime,
        camera_id: str,
        clothing_color: Optional[str],
        confidence: float,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Resolve a person observation to a persistent entity.
        Returns {"entity_id": str, "confidence": float, "method": str, "is_new": bool}.
        """
        window_start = timestamp - timedelta(seconds=PERSON_MATCH_WINDOW_SEC)

        # Find recent persons across any camera within the window (cross-camera support)
        stmt = (
            select(Person, PersonObservation, Observation)
            .join(PersonObservation, Person.person_id == PersonObservation.person_id)
            .join(
                Observation,
                and_(
                    PersonObservation.observation_id == Observation.observation_id,
                    PersonObservation.timestamp_capture == Observation.timestamp_capture,
                ),
            )
            .where(PersonObservation.timestamp_capture >= window_start)
            .where(PersonObservation.timestamp_capture <= timestamp)
            .order_by(PersonObservation.timestamp_capture.desc())
            .limit(50)
        )
        result = await db.execute(stmt)
        candidates = result.all()

        best_score = 0.0
        best_match: Optional[Person] = None
        best_is_same_cam = True

        for person, p_obs, obs in candidates:
            is_same_cam = (obs.source_camera_id == camera_id)
            spatial_score = 1.0

            if not is_same_cam:
                spatial_score = 0.3
                try:
                    from simulator.camera_registry import get_camera
                    cam_a = get_camera(camera_id)
                    cam_b = get_camera(obs.source_camera_id)
                    if cam_a and cam_b:
                        lat1 = cam_a.get("latitude") or cam_a.get("lat", 0)
                        lng1 = cam_a.get("longitude") or cam_a.get("lng", 0)
                        lat2 = cam_b.get("latitude") or cam_b.get("lat", 0)
                        lng2 = cam_b.get("longitude") or cam_b.get("lng", 0)
                        if lat1 and lng1 and lat2 and lng2:
                            dlat = math.radians(lat2 - lat1)
                            dlng = math.radians(lng2 - lng1)
                            a = (
                                math.sin(dlat / 2) ** 2
                                + math.cos(math.radians(lat1))
                                * math.cos(math.radians(lat2))
                                * math.sin(dlng / 2) ** 2
                            )
                            dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                            elapsed_hrs = _diff_seconds(p_obs.timestamp_capture, timestamp) / 3600.0
                            if elapsed_hrs > 0:
                                implied_speed = dist_km / elapsed_hrs
                                # Max plausible speed for pedestrian corridor movement (running/sprint limit)
                                if implied_speed > settings.PHYSICAL_MAX_PEDESTRIAN_SPEED_KMH:
                                    continue  # Skip: physically impossible transit
                                if implied_speed <= 6.0:
                                    spatial_score = max(0.2, 1.0 - (implied_speed / 20.0))
                                else:
                                    spatial_score = max(0.1, 0.7 - (implied_speed / 30.0))
                            else:
                                if dist_km > 0.05:
                                    continue
                                spatial_score = 1.0
                except Exception:
                    spatial_score = 0.5

            attrs = person.attributes or {}
            person_color = attrs.get("clothing_color")
            col_score = _color_similarity(clothing_color, person_color)
            tmp_score = _temporal_proximity(p_obs.timestamp_capture, timestamp, PERSON_MATCH_WINDOW_SEC)

            # Combined score: Clothing color + Temporal proximity + Spatial feasibility
            score = (0.45 * col_score) + (0.30 * tmp_score) + (0.25 * spatial_score)

            if score > best_score:
                best_score = score
                best_match = person
                best_is_same_cam = is_same_cam

        if best_match and best_score >= PERSON_MATCH_THRESHOLD:
            await self._update_person(best_match, timestamp, confidence, clothing_color, db)
            await self._link_person_obs(best_match.person_id, obs_id, timestamp, confidence, db)
            return {
                "entity_id": best_match.person_id,
                "confidence": round(best_score, 3),
                "method": "CLOTHING_TEMPORAL" if best_is_same_cam else "CROSS_CAMERA_SOFT_BIOMETRIC",
                "is_new": False,
            }

        # Create new person
        cam_short = camera_id.replace("cam", "").replace("CAM-", "")[:4]
        new_id = f"P-{cam_short}-{uuid.uuid4().hex[:6]}"

        new_person = Person(
            person_id=new_id,
            first_seen=timestamp,
            last_seen=timestamp,
            observation_count=1,
            running_confidence=confidence,
            attributes={"clothing_color": clothing_color} if clothing_color else {},
        )
        db.add(new_person)
        await self._link_person_obs(new_id, obs_id, timestamp, confidence, db)

        return {"entity_id": new_id, "confidence": 0.50, "method": "NEW_ENTITY", "is_new": True}

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _update_vehicle(self, veh: Vehicle, ts: datetime, conf: float, db: AsyncSession):
        veh.last_seen = ts
        veh.observation_count = (veh.observation_count or 0) + 1

    async def _update_person(self, person: Person, ts: datetime, conf: float, clothing_color: Optional[str], db: AsyncSession):
        person.last_seen = ts
        person.observation_count = (person.observation_count or 0) + 1
        if clothing_color:
            attrs = person.attributes or {}
            attrs["clothing_color"] = clothing_color
            person.attributes = attrs

    async def _link_vehicle_obs(self, vehicle_id: str, obs_id: str, ts: datetime, conf: float, db: AsyncSession):
        link = VehicleObservation(
            vehicle_id=vehicle_id,
            observation_id=obs_id,
            timestamp_capture=ts,
            confidence=conf,
        )
        db.add(link)

    async def _link_person_obs(self, person_id: str, obs_id: str, ts: datetime, conf: float, db: AsyncSession):
        link = PersonObservation(
            person_id=person_id,
            observation_id=obs_id,
            timestamp_capture=ts,
            confidence=conf,
        )
        db.add(link)


# ── Singleton ─────────────────────────────────────────────────────────────────

_resolver: Optional[EntityResolver] = None

def get_entity_resolver() -> EntityResolver:
    global _resolver
    if _resolver is None:
        _resolver = EntityResolver()
    return _resolver
