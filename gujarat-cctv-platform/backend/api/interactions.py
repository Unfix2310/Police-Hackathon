"""
Interaction & Hypothesis API Router — v4.1 §22, §25, §23

Exposes:
    POST /interactions/process-frame        — feed a co-observation into the engine
    GET  /interactions/{entity_id}          — get all interaction events for entity
    GET  /interactions/{entity_id}/active   — get currently active relationships
    GET  /hypotheses/{entity_id}            — list hypotheses for entity
    POST /hypotheses/{hypothesis_id}/review — officer accepts / rejects a hypothesis
    GET  /graph/{entity_type}/{entity_id}   — temporal investigation graph
    GET  /graph/{entity_type}/{entity_id}/timeline — entity timeline (sorted events)
    GET  /graph/{entity_type}/{entity_id}/vehicles — all vehicles an entity used
    POST /graph/shared-passengers           — find shared passengers between two vehicles
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from auth.rbac import require_role
from models.user import User
from models.interaction import InteractionEvent, Hypothesis
from models.enums import HypothesisStatus

from engine.interaction import (
    EntityObservation,
    get_interaction_engine,
    get_correlation_engine,
)
from engine.graph import new_temporal_graph

router = APIRouter(tags=["Interactions & Hypotheses"])


# ══════════════════════════════════════════════════════════════════════════════
# Request / Response schemas
# ══════════════════════════════════════════════════════════════════════════════

class EntityObsPayload(BaseModel):
    entity_id: str
    entity_type: str                  # "PERSON" | "VEHICLE"
    observation_id: str
    camera_id: str
    timestamp: datetime
    bbox: List[int] = Field(..., min_length=4, max_length=4)
    confidence: float
    frame_ref: Optional[str] = None
    location_id: Optional[str] = None
    attributes: dict = {}


class ProcessFrameRequest(BaseModel):
    """Feed a co-observation (person + vehicle in same frame) into the engine."""
    person: EntityObsPayload
    vehicle: EntityObsPayload


class ReviewRequest(BaseModel):
    decision: str             # "ACCEPTED" | "REJECTED" | "DEFERRED"
    notes: Optional[str] = None


class SharedPassengerRequest(BaseModel):
    vehicle_a_id: str
    vehicle_b_id: str


# ══════════════════════════════════════════════════════════════════════════════
# Interaction Event endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/interactions/process-frame")
async def process_co_observation(
    req: ProcessFrameRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "operator", "admin"])),
):
    """
    Feed a co-observed person+vehicle frame into the Interaction Engine.
    Drives the PersonVehicle state machine and persists any transitions
    as InteractionEvent rows.

    Returns the list of new InteractionEvents created (may be empty if no
    state transition occurred).
    """
    engine = get_interaction_engine()

    person_obs = EntityObservation(**req.person.model_dump())
    vehicle_obs = EntityObservation(**req.vehicle.model_dump())

    events = await engine.process_co_observation(person_obs, vehicle_obs, db)

    return {
        "events_created": len(events),
        "events": [_serialize_event(e) for e in events],
    }


@router.get("/interactions/{entity_id}")
async def get_interaction_history(
    entity_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    All InteractionEvents where entity_id is the subject,
    ordered by start_time descending.
    """
    engine = get_interaction_engine()
    events = await engine.get_entity_relationship_history(entity_id, db, limit=limit)
    return {"entity_id": entity_id, "count": len(events), "events": [_serialize_event(e) for e in events]}


@router.get("/interactions/{entity_id}/active")
async def get_active_relationships(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "operator", "admin"])),
):
    """
    Currently ACTIVE relationships (RIDING_IN / ENTERED) for this entity.
    Used for live tracking: "Is Person P-17 currently inside a vehicle?"
    """
    engine = get_interaction_engine()
    events = await engine.get_active_relationships(entity_id, db)
    return {"entity_id": entity_id, "active_count": len(events), "relationships": [_serialize_event(e) for e in events]}


# ══════════════════════════════════════════════════════════════════════════════
# Hypothesis endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/hypotheses/{entity_id}")
async def get_hypotheses(
    entity_id: str,
    status: Optional[str] = Query(None, description="Filter by status: GENERATED, PENDING_REVIEW, ACCEPTED, REJECTED, SUPERSEDED"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    List all hypotheses for an entity.
    The confidence_band and requires_human_review fields tell the UI
    how prominently to surface each hypothesis.

    Critical: hypotheses are decision support, NOT confirmed facts.
    """
    query = select(Hypothesis).where(Hypothesis.primary_entity_id == entity_id)
    if status:
        query = query.where(Hypothesis.status == status)
    query = query.order_by(Hypothesis.confidence.desc())

    result = await db.execute(query)
    hyps = result.scalars().all()

    return {
        "entity_id": entity_id,
        "count": len(hyps),
        "hypotheses": [_serialize_hypothesis(h) for h in hyps],
    }


@router.post("/hypotheses/{entity_id}/generate-trajectory")
async def generate_trajectory_hypothesis(
    entity_id: str,
    entity_type: str = Query("PERSON"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "admin"])),
):
    """
    Trigger the Correlation Engine to generate a TRAJECTORY_LINK hypothesis
    for this entity based on all its InteractionEvents.

    Returns the generated Hypothesis (status=GENERATED, requires_human_review=True).
    """
    engine = get_correlation_engine()
    hyp = await engine.build_trajectory_hypothesis(entity_id, entity_type, db)
    if hyp is None:
        raise HTTPException(status_code=404, detail="No interaction events found for entity")
    return _serialize_hypothesis(hyp)


@router.post("/hypotheses/{hypothesis_id}/review")
async def review_hypothesis(
    hypothesis_id: str,
    req: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    Officer review of a hypothesis.

    This is the ONLY path to accepting a correlation result for operational use.
    A hypothesis that remains GENERATED or PENDING_REVIEW MUST NOT trigger
    any enforcement action.

    Allowed decisions: ACCEPTED | REJECTED | DEFERRED
    """
    if req.decision not in ("ACCEPTED", "REJECTED", "DEFERRED"):
        raise HTTPException(
            status_code=400,
            detail="decision must be one of: ACCEPTED, REJECTED, DEFERRED",
        )

    engine = get_correlation_engine()
    hyp = await engine.officer_review(
        hypothesis_id=hypothesis_id,
        decision=req.decision,
        reviewed_by=user.user_id,
        notes=req.notes,
        db=db,
    )
    if hyp is None:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    return _serialize_hypothesis(hyp)


# ══════════════════════════════════════════════════════════════════════════════
# Temporal Investigation Graph endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/graph/{entity_type}/{entity_id}")
async def get_temporal_graph(
    entity_type: str,
    entity_id: str,
    depth: int = Query(2, ge=1, le=4),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    Build and return the temporal investigation graph centred on entity_id.

    Edges include: start_time, end_time, confidence, evidence_refs, reason_codes.
    Frontend can render this with D3.js or React Flow and filter by time window.
    """
    g = new_temporal_graph()
    await g.build_for_entity(entity_id, entity_type.upper(), db, depth=depth)
    return g.to_dict()


@router.get("/graph/{entity_type}/{entity_id}/timeline")
async def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    Chronological timeline of all relationship events for entity_id.
    Sorted by start_time ascending — used by the Investigator timeline panel.
    """
    g = new_temporal_graph()
    await g.build_for_entity(entity_id, entity_type.upper(), db, depth=1)
    return {
        "entity_id": entity_id,
        "timeline": g.get_entity_timeline(entity_id),
    }


@router.get("/graph/{entity_type}/{entity_id}/vehicles")
async def get_entity_vehicles(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    All vehicles a person has been associated with.
    Powers: "Show me every vehicle Person P-17 has used"
    """
    g = new_temporal_graph()
    await g.build_for_entity(entity_id, entity_type.upper(), db, depth=1)
    return {
        "entity_id": entity_id,
        "vehicles": g.get_entity_vehicles(entity_id),
    }


@router.get("/graph/vehicle/{vehicle_id}/occupants")
async def get_vehicle_occupants_at(
    vehicle_id: str,
    at_time: datetime = Query(..., description="ISO-8601 datetime, e.g. 2026-08-19T18:15:00Z"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command", "admin"])),
):
    """
    §23 Query 1: "Who was inside vehicle_id at time at_time?"
    Returns all persons with an active RIDING_IN edge at the given timestamp.
    """
    g = new_temporal_graph()
    await g.build_for_entity(vehicle_id, "VEHICLE", db, depth=1)
    occupants = g.who_was_in_vehicle_at(vehicle_id, at_time)
    return {"vehicle_id": vehicle_id, "at_time": at_time.isoformat(), "occupants": occupants}


@router.post("/graph/shared-passengers")
async def find_shared_passengers(
    req: SharedPassengerRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "admin"])),
):
    """
    §23 Query 4: "Did vehicle_a and vehicle_b ever share a passenger?"
    Powers the multi-hop vehicle switch investigation scenario.
    """
    g = new_temporal_graph()
    # Build graph covering both vehicles
    await g.build_for_entity(req.vehicle_a_id, "VEHICLE", db, depth=2)
    shared = g.shared_passengers(req.vehicle_a_id, req.vehicle_b_id)
    return {
        "vehicle_a_id": req.vehicle_a_id,
        "vehicle_b_id": req.vehicle_b_id,
        "shared_passenger_ids": shared,
        "has_shared_passengers": len(shared) > 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Serialisation helpers
# ══════════════════════════════════════════════════════════════════════════════

def _serialize_event(ev: InteractionEvent) -> dict:
    return {
        "event_id":             ev.event_id,
        "event_type":           ev.event_type,
        "interaction_class":    ev.interaction_class,
        "subject_entity_id":    ev.subject_entity_id,
        "subject_entity_type":  ev.subject_entity_type,
        "object_entity_id":     ev.object_entity_id,
        "object_entity_type":   ev.object_entity_type,
        "camera_id":            ev.camera_id,
        "location_id":          ev.location_id,
        "start_time":           ev.start_time.isoformat() if ev.start_time else None,
        "end_time":             ev.end_time.isoformat() if ev.end_time else None,
        "confidence":           ev.confidence,
        "generic_lifecycle":    ev.generic_lifecycle,
        "domain_state_before":  ev.domain_state_before,
        "domain_state_after":   ev.domain_state_after,
        "reason_codes":         ev.reason_codes or [],
        "contributing_factors": ev.contributing_factors or [],
        "evidence_obs_ids":     ev.evidence_obs_ids or [],
        "source_frame_refs":    ev.source_frame_refs or [],
        "model_version":        ev.model_version,
        "created_at":           ev.created_at.isoformat() if ev.created_at else None,
    }


def _serialize_hypothesis(h: Hypothesis) -> dict:
    return {
        "hypothesis_id":           h.hypothesis_id,
        "claim":                   h.claim,
        "hypothesis_type":         h.hypothesis_type,
        "confidence":              h.confidence,
        "confidence_band":         h.confidence_band,
        "scoring_maturity":        h.scoring_maturity,
        "scoring_method":          h.scoring_method,
        "status":                  h.status,
        "requires_human_review":   h.requires_human_review,
        "supporting_interactions": h.supporting_interactions or [],
        "supporting_observations": h.supporting_observations or [],
        "reason_codes":            h.reason_codes or [],
        "contributing_factors":    h.contributing_factors or [],
        "alternative_hypotheses":  h.alternative_hypotheses or [],
        "primary_entity_id":       h.primary_entity_id,
        "primary_entity_type":     h.primary_entity_type,
        "reviewed_by":             h.reviewed_by,
        "review_timestamp":        h.review_timestamp.isoformat() if h.review_timestamp else None,
        "review_decision":         h.review_decision,
        "review_notes":            h.review_notes,
        "model_version":           h.model_version,
        "created_at":              h.created_at.isoformat() if h.created_at else None,
    }
