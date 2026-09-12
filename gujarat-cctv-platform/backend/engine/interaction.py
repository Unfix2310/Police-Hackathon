"""
Interaction Engine — v4.1 §21, §22, §10

Detects, classifies, and persists dynamic relationship events between entities.
This is the core of the "dynamic entity" layer in the v4.1 architecture.

Architecture:
    Entity observations come in from the Entity Engine.
    The Interaction Engine watches pairs of entities and drives a state machine
    through the Person–Vehicle domain states (§10):

        UNKNOWN → POSSIBLE_PROXIMITY → POSSIBLE_ENTRY
               → ENTERED → RIDING_IN → POSSIBLE_EXIT → EXITED → ENDED

    On every state transition, an InteractionEvent is persisted and published
    so the Correlation Engine and Temporal Graph can consume it.

Contract:
    Input:  Two entity observations (person + vehicle) with timestamps, camera IDs,
            bounding boxes, and locations.
    Output: InteractionEvent (canonical v4.1 §22 contract) saved to DB.
"""

from __future__ import annotations

import uuid
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.interaction import InteractionEvent, Hypothesis
from models.enums import (
    GenericLifecycleState,
    PersonVehicleDomainState,
    InteractionClass,
    EventType,
    HypothesisType,
    ConfidenceBand,
    HypothesisStatus,
)

logger = logging.getLogger("cctv_platform.interaction")


# ── Domain state → Generic lifecycle mapping (v4.1 §10) ──────────────────────

_PV_STATE_TO_GENERIC: Dict[str, str] = {
    PersonVehicleDomainState.UNKNOWN:            GenericLifecycleState.NO_ASSOCIATION,
    PersonVehicleDomainState.POSSIBLE_PROXIMITY: GenericLifecycleState.CANDIDATE,
    PersonVehicleDomainState.POSSIBLE_ENTRY:     GenericLifecycleState.PROBABLE,
    PersonVehicleDomainState.ENTERED:            GenericLifecycleState.ACTIVE,
    PersonVehicleDomainState.RIDING_IN:          GenericLifecycleState.ACTIVE,
    PersonVehicleDomainState.POSSIBLE_EXIT:      GenericLifecycleState.ACTIVE,
    PersonVehicleDomainState.EXITED:             GenericLifecycleState.ENDED,
    PersonVehicleDomainState.ENDED:              GenericLifecycleState.ENDED,
}

_PV_DOMAIN_TO_EVENT: Dict[str, str] = {
    PersonVehicleDomainState.POSSIBLE_PROXIMITY: EventType.APPROACHED,
    PersonVehicleDomainState.POSSIBLE_ENTRY:     EventType.APPROACHED,
    PersonVehicleDomainState.ENTERED:            EventType.ENTERED,
    PersonVehicleDomainState.RIDING_IN:          EventType.RIDING_IN,
    PersonVehicleDomainState.EXITED:             EventType.EXITED,
    PersonVehicleDomainState.ENDED:              EventType.EXITED,
}


# ── Observation snapshot (input to the engine) ────────────────────────────────

@dataclass
class EntityObservation:
    """
    Lightweight snapshot of one entity observation.
    The full Observation row lives in the observations table;
    this carries only what the Interaction Engine needs.
    """
    entity_id: str
    entity_type: str          # "PERSON" | "VEHICLE"
    observation_id: str
    camera_id: str
    timestamp: datetime
    bbox: List[int]           # [x1, y1, x2, y2] in pixels
    confidence: float
    frame_ref: Optional[str] = None
    location_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _iou(box_a: List[int], box_b: List[int]) -> float:
    """Intersection-over-Union of two bounding boxes [x1,y1,x2,y2]."""
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _bbox_centre(box: List[int]) -> Tuple[float, float]:
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def _centre_distance_px(box_a: List[int], box_b: List[int]) -> float:
    ax, ay = _bbox_centre(box_a)
    bx, by = _bbox_centre(box_b)
    return math.hypot(ax - bx, ay - by)


def _box_height(box: List[int]) -> float:
    return float(box[3] - box[1])


def _proximity_score(person_box: List[int], vehicle_box: List[int]) -> float:
    """
    Returns 0-1 proximity score.
    1.0 = centres within 0.3× vehicle box height (very close).
    0.0 = centres more than 2× vehicle box height apart.
    """
    dist = _centre_distance_px(person_box, vehicle_box)
    vh = _box_height(vehicle_box) or 1.0
    ratio = dist / vh
    if ratio <= 0.3:
        return 1.0
    elif ratio <= 2.0:
        return max(0.0, 1.0 - (ratio - 0.3) / 1.7)
    return 0.0


def _overlap_score(person_box: List[int], vehicle_box: List[int]) -> float:
    """
    Fraction of person bbox that overlaps the vehicle bbox.
    Used to detect person entering / inside vehicle.
    """
    xa = max(person_box[0], vehicle_box[0])
    ya = max(person_box[1], vehicle_box[1])
    xb = min(person_box[2], vehicle_box[2])
    yb = min(person_box[3], vehicle_box[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    area_person = (person_box[2] - person_box[0]) * (person_box[3] - person_box[1])
    return inter / area_person if area_person > 0 else 0.0


# ── State machine thresholds ──────────────────────────────────────────────────

class _Thresholds:
    PROXIMITY_FOR_CANDIDATE = 0.50   # proximity_score > this → POSSIBLE_PROXIMITY
    OVERLAP_FOR_ENTRY       = 0.40   # overlap_score > this → POSSIBLE_ENTRY
    OVERLAP_FOR_ENTERED     = 0.70   # overlap_score > this → ENTERED
    PROXIMITY_FOR_EXIT      = 0.65   # proximity_score < this while RIDING_IN → POSSIBLE_EXIT
    SEPARATION_FOR_EXITED   = 0.30   # proximity_score < this after POSSIBLE_EXIT → EXITED


# ── Person–Vehicle state machine ──────────────────────────────────────────────

class PersonVehicleStateMachine:
    """
    Drives the Person–Vehicle relationship through v4.1 §10 domain states.

    One instance per (person_id, vehicle_id) pair.
    Call update() each time both entities appear in the same camera frame.
    """

    def __init__(self, person_id: str, vehicle_id: str):
        self.person_id = person_id
        self.vehicle_id = vehicle_id
        self.state = PersonVehicleDomainState.UNKNOWN
        self._frames_in_state: int = 0
        self._last_person_obs: Optional[EntityObservation] = None
        self._last_vehicle_obs: Optional[EntityObservation] = None

    # ── Public API ──────────────────────────────────────────────────────

    def update(
        self,
        person_obs: EntityObservation,
        vehicle_obs: EntityObservation,
    ) -> Optional[Dict[str, Any]]:
        """
        Feed one co-observed frame into the state machine.

        Returns a transition dict if a new InteractionEvent should be created,
        or None if the state did not change.
        """
        self._frames_in_state += 1
        old_state = self.state
        proximity = _proximity_score(person_obs.bbox, vehicle_obs.bbox)
        overlap = _overlap_score(person_obs.bbox, vehicle_obs.bbox)

        new_state, reasons, factors = self._next_state(proximity, overlap)

        self._last_person_obs = person_obs
        self._last_vehicle_obs = vehicle_obs

        if new_state == old_state:
            # Emit a RIDING_IN heartbeat every ~30 frames while active
            if new_state == PersonVehicleDomainState.RIDING_IN and self._frames_in_state % 30 == 0:
                return self._build_transition(
                    old_state, new_state, person_obs, vehicle_obs,
                    reasons, factors, confidence=0.90,
                )
            return None

        self.state = new_state
        self._frames_in_state = 0
        return self._build_transition(
            old_state, new_state, person_obs, vehicle_obs,
            reasons, factors,
        )

    def person_disappeared(
        self,
        vehicle_obs: EntityObservation,
        timestamp: datetime,
    ) -> Optional[Dict[str, Any]]:
        """
        Called when person is no longer detected but vehicle is still visible.
        If we were in POSSIBLE_ENTRY or RIDING_IN → confirm ENTERED/RIDING_IN.
        """
        if self.state in (PersonVehicleDomainState.POSSIBLE_ENTRY,
                          PersonVehicleDomainState.ENTERED):
            old = self.state
            self.state = PersonVehicleDomainState.RIDING_IN
            self._frames_in_state = 0
            return self._build_transition(
                old, self.state, self._last_person_obs, vehicle_obs,
                reasons=["person_disappeared_inside_vehicle"],
                factors=["no_person_bbox_vehicle_present"],
                confidence=0.85,
                timestamp_override=timestamp,
            )
        return None

    def vehicle_stopped(
        self,
        person_obs: Optional[EntityObservation],
        vehicle_obs: EntityObservation,
        timestamp: datetime,
    ) -> Optional[Dict[str, Any]]:
        """
        Called when vehicle stops while in RIDING_IN state.
        Transitions to POSSIBLE_EXIT.
        """
        if self.state == PersonVehicleDomainState.RIDING_IN:
            old = self.state
            self.state = PersonVehicleDomainState.POSSIBLE_EXIT
            self._frames_in_state = 0
            return self._build_transition(
                old, self.state,
                person_obs or self._last_person_obs,
                vehicle_obs,
                reasons=["vehicle_stopped"],
                factors=["vehicle_stationary"],
                confidence=0.70,
                timestamp_override=timestamp,
            )
        return None

    # ── Internal state transition logic ─────────────────────────────────

    def _next_state(
        self,
        proximity: float,
        overlap: float,
    ) -> Tuple[str, List[str], List[str]]:
        """Pure function — given sensor scores return (next_state, reasons, factors)."""
        T = _Thresholds
        reasons: List[str] = []
        factors: List[str] = [
            f"proximity_score_{proximity:.2f}",
            f"overlap_score_{overlap:.2f}",
        ]

        if self.state == PersonVehicleDomainState.UNKNOWN:
            if proximity > T.PROXIMITY_FOR_CANDIDATE:
                reasons.append("person_vehicle_proximity_detected")
                return PersonVehicleDomainState.POSSIBLE_PROXIMITY, reasons, factors

        elif self.state == PersonVehicleDomainState.POSSIBLE_PROXIMITY:
            if overlap > T.OVERLAP_FOR_ENTRY:
                reasons.append("person_vehicle_spatial_overlap")
                if overlap > T.OVERLAP_FOR_ENTERED:
                    reasons.append("high_overlap_strong_entry_signal")
                    return PersonVehicleDomainState.POSSIBLE_ENTRY, reasons, factors
                return PersonVehicleDomainState.POSSIBLE_ENTRY, reasons, factors
            if proximity < T.PROXIMITY_FOR_CANDIDATE:
                reasons.append("proximity_dropped_below_threshold")
                return PersonVehicleDomainState.UNKNOWN, reasons, factors

        elif self.state == PersonVehicleDomainState.POSSIBLE_ENTRY:
            if overlap > T.OVERLAP_FOR_ENTERED:
                reasons.append("entry_confirmed_by_overlap")
                return PersonVehicleDomainState.ENTERED, reasons, factors

        elif self.state == PersonVehicleDomainState.ENTERED:
            # Immediately transition to RIDING_IN once entered
            reasons.append("entity_relationship_active")
            return PersonVehicleDomainState.RIDING_IN, reasons, factors

        elif self.state == PersonVehicleDomainState.RIDING_IN:
            # Fix 1a: RIDING_IN exit branch — if person drifts away from vehicle
            # while both are still co-observed, drive POSSIBLE_EXIT through update()
            # without requiring an external vehicle_stopped() trigger.
            if proximity < T.PROXIMITY_FOR_EXIT:
                reasons.append("person_drifting_from_vehicle_while_riding")
                return PersonVehicleDomainState.POSSIBLE_EXIT, reasons, factors

        elif self.state == PersonVehicleDomainState.POSSIBLE_EXIT:
            if proximity < T.SEPARATION_FOR_EXITED:
                reasons.append("person_separated_from_vehicle")
                return PersonVehicleDomainState.EXITED, reasons, factors
            if overlap > T.OVERLAP_FOR_ENTRY:
                reasons.append("false_alarm_person_still_inside")
                return PersonVehicleDomainState.RIDING_IN, reasons, factors

        elif self.state == PersonVehicleDomainState.EXITED:
            # Fix 1b: EXITED → ENDED once person is clearly clear of the vehicle
            # (proximity has stayed low for at least one more co-observed frame).
            if proximity < T.SEPARATION_FOR_EXITED:
                reasons.append("exit_confirmed_person_clear_of_vehicle")
                return PersonVehicleDomainState.ENDED, reasons, factors
            # Person walked back near vehicle after EXITED — new approach
            if proximity > T.PROXIMITY_FOR_CANDIDATE:
                reasons.append("person_returned_to_vehicle_after_exit")
                return PersonVehicleDomainState.POSSIBLE_PROXIMITY, reasons, factors

        return self.state, [], factors  # No change

    def _build_transition(
        self,
        old_state: str,
        new_state: str,
        person_obs: Optional[EntityObservation],
        vehicle_obs: Optional[EntityObservation],
        reasons: List[str],
        factors: List[str],
        confidence: Optional[float] = None,
        timestamp_override: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Build the InteractionEvent payload dict for this transition."""
        ts = timestamp_override or (
            person_obs.timestamp if person_obs else datetime.now(timezone.utc)
        )
        cam_id = (
            (person_obs.camera_id if person_obs else None)
            or (vehicle_obs.camera_id if vehicle_obs else None)
        )
        obs_ids = []
        frame_refs = []
        if person_obs:
            obs_ids.append(person_obs.observation_id)
            if person_obs.frame_ref:
                frame_refs.append(person_obs.frame_ref)
        if vehicle_obs:
            obs_ids.append(vehicle_obs.observation_id)
            if vehicle_obs.frame_ref:
                frame_refs.append(vehicle_obs.frame_ref)

        # Derive confidence from overlap/proximity signals if not given
        if confidence is None:
            confidence = _derive_confidence(old_state, new_state, person_obs, vehicle_obs)

        event_type = _PV_DOMAIN_TO_EVENT.get(new_state, EventType.ASSOCIATED_WITH)
        generic = _PV_STATE_TO_GENERIC.get(new_state, GenericLifecycleState.CANDIDATE)

        return {
            "event_id":          f"IE-{uuid.uuid4().hex[:8].upper()}",
            "event_type":        event_type,
            "interaction_class": InteractionClass.PERSON_VEHICLE,
            "subject_entity_id": self.person_id,
            "subject_entity_type": "PERSON",
            "object_entity_id":  self.vehicle_id,
            "object_entity_type": "VEHICLE",
            "camera_id":         cam_id,
            "location_id":       (person_obs.location_id if person_obs else None),
            "start_time":        ts,
            "end_time":          None,
            "confidence":        round(confidence, 3),
            "generic_lifecycle": generic,
            "domain_state_before": old_state,
            "domain_state_after":  new_state,
            "reason_codes":        reasons,
            "contributing_factors": factors,
            "evidence_obs_ids":    obs_ids,
            "source_frame_refs":   frame_refs,
            "model_version":       "interaction-v1.0.0",
        }


def _derive_confidence(
    old_state: str,
    new_state: str,
    person_obs: Optional[EntityObservation],
    vehicle_obs: Optional[EntityObservation],
) -> float:
    """Heuristic confidence derivation when not overridden."""
    base = 0.70
    if new_state == PersonVehicleDomainState.ENTERED:
        base = 0.87
    elif new_state == PersonVehicleDomainState.RIDING_IN:
        base = 0.90
    elif new_state == PersonVehicleDomainState.EXITED:
        base = 0.85
    elif new_state == PersonVehicleDomainState.POSSIBLE_ENTRY:
        base = 0.72
    elif new_state in (PersonVehicleDomainState.POSSIBLE_PROXIMITY,
                       PersonVehicleDomainState.POSSIBLE_EXIT):
        base = 0.60
    if person_obs:
        base = base * 0.9 + person_obs.confidence * 0.1
    return min(1.0, base)


# ── Interaction Engine (stateful, per-process singleton) ──────────────────────

class InteractionEngine:
    """
    v4.1 §21, §22 — Interaction Engine.

    Manages one PersonVehicleStateMachine per active (person, vehicle) pair.
    State machines are kept in-memory during a session; transitions are
    persisted to the interaction_events table and propagated to the
    Correlation Engine via the event backbone (Redis in MVP).

    Usage (called by the AI pipeline after entity resolution):

        engine = get_interaction_engine()
        events = await engine.process_co_observation(
            person_obs=...,
            vehicle_obs=...,
            db=session,
        )
    """

    def __init__(self):
        # (person_id, vehicle_id) → PersonVehicleStateMachine
        self._pv_machines: Dict[Tuple[str, str], PersonVehicleStateMachine] = {}

    # ── Public methods ───────────────────────────────────────────────────

    async def process_co_observation(
        self,
        person_obs: EntityObservation,
        vehicle_obs: EntityObservation,
        db: AsyncSession,
    ) -> List[InteractionEvent]:
        """
        Process a frame in which both a person and a vehicle are detected.

        Returns list of InteractionEvent rows persisted to DB.
        """
        key = (person_obs.entity_id, vehicle_obs.entity_id)
        machine = self._pv_machines.setdefault(
            key,
            PersonVehicleStateMachine(person_obs.entity_id, vehicle_obs.entity_id),
        )

        transition = machine.update(person_obs, vehicle_obs)
        if transition is None:
            return []

        event = await self._persist_event(transition, db)
        if event is None:
            return []   # false alarm resolved — nothing new to report
        logger.info(
            "InteractionEvent %s: %s %s→%s (conf %.2f)",
            event.event_id,
            f"{person_obs.entity_id}↔{vehicle_obs.entity_id}",
            transition["domain_state_before"],
            transition["domain_state_after"],
            event.confidence,
        )
        return [event]

    async def notify_person_disappeared(
        self,
        person_id: str,
        vehicle_obs: EntityObservation,
        timestamp: datetime,
        db: AsyncSession,
    ) -> List[InteractionEvent]:
        """
        Call when a person entity drops off the tracker while a vehicle
        they were near is still visible. Drives the RIDING_IN confirmation.
        """
        events = []
        for (pid, vid), machine in list(self._pv_machines.items()):
            if pid == person_id:
                transition = machine.person_disappeared(vehicle_obs, timestamp)
                if transition:
                    event = await self._persist_event(transition, db)
                    if event is not None:
                        events.append(event)
        return events

    async def notify_vehicle_stopped(
        self,
        vehicle_id: str,
        vehicle_obs: EntityObservation,
        timestamp: datetime,
        db: AsyncSession,
    ) -> List[InteractionEvent]:
        """
        Call when a vehicle stops. Triggers POSSIBLE_EXIT for all persons
        currently in RIDING_IN state with that vehicle.
        """
        events = []
        for (pid, vid), machine in list(self._pv_machines.items()):
            if vid == vehicle_id:
                transition = machine.vehicle_stopped(None, vehicle_obs, timestamp)
                if transition:
                    event = await self._persist_event(transition, db)
                    if event is not None:
                        events.append(event)
        return events

    async def get_active_relationships(
        self, entity_id: str, db: AsyncSession
    ) -> List[InteractionEvent]:
        """
        Fetch all ACTIVE InteractionEvents involving this entity
        (i.e. end_time is NULL and domain_state_after is RIDING_IN or ENTERED).
        """
        result = await db.execute(
            select(InteractionEvent).where(
                and_(
                    InteractionEvent.subject_entity_id == entity_id,
                    InteractionEvent.end_time.is_(None),
                    InteractionEvent.domain_state_after.in_([
                        PersonVehicleDomainState.RIDING_IN,
                        PersonVehicleDomainState.ENTERED,
                    ]),
                )
            ).order_by(desc(InteractionEvent.start_time))
        )
        return list(result.scalars().all())

    async def get_entity_relationship_history(
        self,
        entity_id: str,
        db: AsyncSession,
        limit: int = 50,
    ) -> List[InteractionEvent]:
        """
        Return all InteractionEvents where this entity is subject OR object,
        ordered by start_time descending. Powers the temporal timeline.

        Fix 2 (query): the original query only fetched subject_entity_id == entity_id.
        A vehicle queried directly would get zero results because its passengers
        appear as subjects. The OR clause below fixes this for both directions.
        """
        from sqlalchemy import or_
        result = await db.execute(
            select(InteractionEvent).where(
                or_(
                    InteractionEvent.subject_entity_id == entity_id,
                    InteractionEvent.object_entity_id == entity_id,
                )
            ).order_by(desc(InteractionEvent.start_time)).limit(limit)
        )
        return list(result.scalars().all())


    # ── Internal helpers ─────────────────────────────────────────────────

    # States that signal the open relationship has ended — the previous
    # RIDING_IN / ENTERED event must have its end_time set.
    _CLOSING_STATES = frozenset([
        PersonVehicleDomainState.EXITED,
        PersonVehicleDomainState.ENDED,
    ])

    async def _persist_event(
        self, payload: Dict[str, Any], db: AsyncSession
    ) -> Optional[InteractionEvent]:
        """
        Save an InteractionEvent to the database.

        Fix 1c (end_time close): if this transition is a closing state
        (EXITED / ENDED), find the most recent open
        RIDING_IN or ENTERED event for the same (subject, object) pair
        and stamp its end_time = this event's start_time. This gives
        RIDING_IN edges meaningful end_times for the temporal graph
        (v4.1 §23 query 1 depends on this).

        Returns None when a false-alarm POSSIBLE_EXIT→RIDING_IN reversion
        is resolved by an existing open row (no new event created).
        """
        new_state_after = payload.get("domain_state_after", "")

        # Prevent false-alarm reversion from creating a fragmented RIDING_IN row
        if payload.get("domain_state_before") == PersonVehicleDomainState.POSSIBLE_EXIT and \
           new_state_after == PersonVehicleDomainState.RIDING_IN:
            open_result = await db.execute(
                select(InteractionEvent).where(
                    and_(
                        InteractionEvent.subject_entity_id == payload["subject_entity_id"],
                        InteractionEvent.object_entity_id == payload["object_entity_id"],
                        InteractionEvent.domain_state_after == PersonVehicleDomainState.RIDING_IN,
                        InteractionEvent.end_time.is_(None)
                    )
                ).order_by(desc(InteractionEvent.start_time)).limit(1)
            )
            open_event = open_result.scalar_one_or_none()
            if open_event is not None:
                logger.debug("False alarm resolved: no new event created")
                return None
        if new_state_after in self._CLOSING_STATES:
            # Close the open riding event for this pair
            open_result = await db.execute(
                select(InteractionEvent).where(
                    and_(
                        InteractionEvent.subject_entity_id == payload["subject_entity_id"],
                        InteractionEvent.object_entity_id == payload["object_entity_id"],
                        InteractionEvent.end_time.is_(None),
                        InteractionEvent.domain_state_after.in_([
                            PersonVehicleDomainState.RIDING_IN,
                            PersonVehicleDomainState.ENTERED,
                        ]),
                    )
                ).order_by(desc(InteractionEvent.start_time)).limit(1)
            )
            open_event = open_result.scalar_one_or_none()
            if open_event is not None:
                open_event.end_time = payload["start_time"]
                logger.debug(
                    "Closed event %s end_time=%s (→ %s)",
                    open_event.event_id, payload["start_time"], new_state_after,
                )

        event = InteractionEvent(**payload)
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event



# ── Correlation Engine (builds Hypotheses from InteractionEvents) ─────────────

class CorrelationEngine:
    """
    v4.1 §17, §25 — Correlation Engine.

    Takes a sequence of InteractionEvents for an entity and produces
    Hypothesis objects with confidence bands and human-review flags.

    Key principle: Results are ALWAYS wrapped as Hypothesis — never as facts.
    status starts at GENERATED, must be ACCEPTED by an officer before any
    operational action is taken (§25).
    """

    # ── Association scoring weights (v4.1 §17) ────────────────────────────────
    #
    # STATUS: MVP-heuristic (v4.1 §17 classification).
    #
    # These weights are initial engineering estimates. v4.1 §17 requires
    # calibration against a ground-truth annotated dataset before production.
    # The calibration pipeline (Step 1–6 in §17) has not yet been run;
    # these values produce reasonable MVP behaviour but MUST NOT be
    # presented as validated production weights.
    #
    # When ground-truth calibration is complete, replace these values and
    # update the classification from "MVP-heuristic" to "Calibrated" in §17.
    #
    # Note: W_IDENTITY, W_DIRECTION, W_TOPOLOGY, W_APPEARANCE are carried
    # as named constants for traceability — they are not yet wired into
    # every scorer because not all input signals are available at MVP scale.
    # Only W_TEMPORAL and W_SPATIAL are actively used below.
    W_IDENTITY   = 0.35   # exact plate / ReID match  [not yet wired — no ground-truth]
    W_TEMPORAL   = 0.20   # temporal proximity / gap penalty      [WIRED below]
    W_SPATIAL    = 0.20   # route feasibility score               [WIRED below]
    W_APPEARANCE = 0.15   # appearance similarity (ReID cosine)  [not yet wired]
    W_DIRECTION  = 0.05   # direction of travel consistency      [not yet wired]
    W_TOPOLOGY   = 0.05   # camera network topology score        [not yet wired]


    async def build_trajectory_hypothesis(
        self,
        entity_id: str,
        entity_type: str,
        db: AsyncSession,
    ) -> Optional[Hypothesis]:
        """
        Build a TRAJECTORY_LINK hypothesis for an entity based on all
        its InteractionEvents. Wraps the trajectory claim with confidence
        and requires human review before operational use.
        """
        events_result = await db.execute(
            select(InteractionEvent).where(
                InteractionEvent.subject_entity_id == entity_id,
            ).order_by(InteractionEvent.start_time)
        )
        events: List[InteractionEvent] = list(events_result.scalars().all())

        if not events:
            return None

        # Build trajectory claim string
        hops = []
        for ev in events:
            if ev.event_type in (EventType.ENTERED, EventType.RIDING_IN, EventType.EXITED):
                hops.append(
                    f"{ev.event_type} {ev.object_entity_id or ''} "
                    f"at {ev.start_time.strftime('%H:%M')}"
                )
        claim = f"Entity {entity_id} trajectory: " + " → ".join(hops) if hops else (
            f"Entity {entity_id} observed at {len(events)} interaction points"
        )

        # Score = average confidence of supporting events (simplified)
        score = sum(e.confidence for e in events) / len(events) if events else 0.5
        band = ConfidenceBand.from_score(score)

        hyp_id = f"HYP-{uuid.uuid4().hex[:8].upper()}"
        hyp = Hypothesis(
            hypothesis_id=hyp_id,
            claim=claim,
            hypothesis_type=HypothesisType.TRAJECTORY_LINK,
            confidence=round(score, 3),
            confidence_band=band,
            scoring_maturity="mvp_partial",
            scoring_method="naive_average_fallback",
            supporting_observations=[],
            supporting_interactions=[e.event_id for e in events],
            reason_codes=["trajectory_from_interaction_events"],
            contributing_factors=[
                {"factor": "event_count", "value": len(events)},
                {"factor": "average_confidence", "value": round(score, 3)}
            ],
            alternative_hypotheses=[],
            status=HypothesisStatus.GENERATED,
            requires_human_review=True,
            primary_entity_id=entity_id,
            primary_entity_type=entity_type,
            model_version="correlation-v1.0.0",
        )
        db.add(hyp)
        await db.commit()
        await db.refresh(hyp)
        logger.info(
            "Hypothesis %s created: %s (band=%s, conf=%.2f)",
            hyp_id, claim[:80], band, score,
        )
        return hyp

    async def build_vehicle_switch_hypothesis(
        self,
        person_id: str,
        vehicle_a_id: str,
        vehicle_b_id: str,
        exit_event: InteractionEvent,
        entry_event: InteractionEvent,
        db: AsyncSession,
    ) -> Hypothesis:
        """
        Build a VEHICLE_SWITCH hypothesis when a person exits one vehicle
        and enters another within a plausible time/distance window.
        """
        time_gap_s = (
            entry_event.start_time - exit_event.start_time
        ).total_seconds()

        # Temporal score: 1.0 at gap=0s, 0.0 at gap>=600s (10-min window).
        # Uses W_TEMPORAL (MVP-heuristic, see weight block above).
        temporal_score = max(0.0, 1.0 - time_gap_s / 600.0)

        # Spatial score: average confidence of the two bounding events.
        # This is a proxy for spatial certainty — proper route feasibility
        # (from feasibility.py) would replace this when camera GPS data is wired.
        spatial_score = (exit_event.confidence + entry_event.confidence) / 2.0

        # Weighted combination using the named class constants (§17 formula).
        # Remaining weights (W_IDENTITY, W_APPEARANCE, etc.) are zero here
        # because those signals aren't available at vehicle-switch detection time.
        remaining_w = 1.0 - self.W_TEMPORAL - self.W_SPATIAL
        score = round(
            self.W_TEMPORAL * temporal_score
            + self.W_SPATIAL * spatial_score
            + remaining_w * spatial_score,   # fallback: spatial fills the gap
            3,
        )

        claim = (
            f"Person {person_id} switched from vehicle {vehicle_a_id} "
            f"to vehicle {vehicle_b_id} "
            f"(gap {time_gap_s:.0f}s, conf {score:.2f})"
        )
        hyp = Hypothesis(
            hypothesis_id=f"HYP-{uuid.uuid4().hex[:8].upper()}",
            claim=claim,
            hypothesis_type=HypothesisType.VEHICLE_SWITCH,
            confidence=score,
            confidence_band=ConfidenceBand.from_score(score),
            scoring_maturity="mvp_partial",
            scoring_method="weighted_heuristic_v1",
            supporting_observations=[],
            supporting_interactions=[exit_event.event_id, entry_event.event_id],
            reason_codes=["person_exited_vehicle_a", "person_entered_vehicle_b"],
            contributing_factors=[
                {"factor": "temporal_score", "value": round(temporal_score, 3), "effective_weight": self.W_TEMPORAL},
                {"factor": "spatial_score", "value": round(spatial_score, 3), "effective_weight": round(self.W_SPATIAL + remaining_w, 3)},
                {"factor": "time_gap_seconds", "value": round(time_gap_s, 1)}
            ],
            alternative_hypotheses=[],
            status=HypothesisStatus.GENERATED,
            requires_human_review=True,
            primary_entity_id=person_id,
            primary_entity_type="PERSON",
            model_version="correlation-v1.0.0",
        )
        db.add(hyp)
        await db.commit()
        await db.refresh(hyp)
        return hyp

    async def officer_review(
        self,
        hypothesis_id: str,
        decision: str,       # "ACCEPTED" | "REJECTED" | "DEFERRED"
        reviewed_by: str,    # user_id
        notes: Optional[str],
        db: AsyncSession,
    ) -> Optional[Hypothesis]:
        """
        Record an officer's review decision on a hypothesis.
        This is the ONLY path to moving status past PENDING_REVIEW.
        """
        result = await db.execute(
            select(Hypothesis).where(Hypothesis.hypothesis_id == hypothesis_id)
        )
        hyp = result.scalar_one_or_none()
        if hyp is None:
            return None

        hyp.status = decision
        hyp.reviewed_by = reviewed_by
        hyp.review_timestamp = datetime.now(timezone.utc)
        hyp.review_decision = decision
        hyp.review_notes = notes
        await db.commit()
        await db.refresh(hyp)
        logger.info(
            "Hypothesis %s reviewed by %s: %s", hypothesis_id, reviewed_by, decision
        )
        return hyp


# ── Module-level singletons ───────────────────────────────────────────────────

_interaction_engine: Optional[InteractionEngine] = None
_correlation_engine: Optional[CorrelationEngine] = None


def get_interaction_engine() -> InteractionEngine:
    global _interaction_engine
    if _interaction_engine is None:
        _interaction_engine = InteractionEngine()
    return _interaction_engine


def get_correlation_engine() -> CorrelationEngine:
    global _correlation_engine
    if _correlation_engine is None:
        _correlation_engine = CorrelationEngine()
    return _correlation_engine
