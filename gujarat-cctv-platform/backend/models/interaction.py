"""
Interaction Event & Hypothesis SQLAlchemy Models.

Implements v4.1 §22 (InteractionEvent contract) and §25 (Hypothesis contract).
These two tables are the core of the dynamic entity relationship layer.
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Boolean, JSON, Index
from datetime import datetime, timezone
from typing import Optional, Any
from database import Base


class InteractionEvent(Base):
    """
    v4.1 §22 — InteractionEvent canonical contract.

    Records a single classified relationship event between two entities.
    e.g. "Person P-17 ENTERED Vehicle V-4521 at 18:14 with confidence 0.87"

    Every field in this table corresponds exactly to a field in the
    InteractionEvent contract defined in §22.
    """
    __tablename__ = "interaction_events"

    # ── Identity ──────────────────────────────────────────────────────────────
    event_id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # ── Classification ────────────────────────────────────────────────────────
    # e.g. "ENTERED", "EXITED", "RIDING_IN", "CO_LOCATED", "FOLLOWED", ...
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. "PERSON_VEHICLE", "PERSON_PERSON", "VEHICLE_VEHICLE", ...
    interaction_class: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Entities involved ─────────────────────────────────────────────────────
    subject_entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subject_entity_type: Mapped[str] = mapped_column(String(20), nullable=False)   # PERSON | VEHICLE
    object_entity_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    object_entity_type: Mapped[Optional[str]] = mapped_column(String(20))          # PERSON | VEHICLE | LOCATION

    # ── Source provenance ─────────────────────────────────────────────────────
    camera_id: Mapped[Optional[str]] = mapped_column(String(50))
    location_id: Mapped[Optional[str]] = mapped_column(String(100))

    # ── Temporal bounds ───────────────────────────────────────────────────────
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))   # null = ongoing

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # ── State machine ─────────────────────────────────────────────────────────
    # v4.1 §10: two-level state model
    generic_lifecycle: Mapped[str] = mapped_column(String(30), nullable=False)
    # e.g. CANDIDATE | PROBABLE | ACTIVE | ENDED | RE_EVALUATED
    domain_state_before: Mapped[Optional[str]] = mapped_column(String(50))
    domain_state_after: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Explainability ────────────────────────────────────────────────────────
    # Stored as JSON arrays of strings
    reason_codes: Mapped[Optional[list]] = mapped_column(JSON)
    # e.g. ["bbox_overlap_0.72", "door_proximity_0.85"]
    contributing_factors: Mapped[Optional[list]] = mapped_column(JSON)

    # ── Evidence provenance (v4.1 §26) ────────────────────────────────────────
    evidence_obs_ids: Mapped[Optional[list]] = mapped_column(JSON)    # Observation IDs
    source_frame_refs: Mapped[Optional[list]] = mapped_column(JSON)   # Frame references

    # ── Model metadata ────────────────────────────────────────────────────────
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ie_subject_time", "subject_entity_id", "start_time"),
        Index("ix_ie_object_time", "object_entity_id", "start_time"),
        Index("ix_ie_type_class", "event_type", "interaction_class"),
    )


class Hypothesis(Base):
    """
    v4.1 §25 — Hypothesis canonical contract.

    A correlation result wrapped as a reviewable hypothesis — NEVER a confirmed fact.
    The system surfaces these to investigators who must accept/reject before any
    operational action is taken.

    Key rule: requires_human_review is always True for new hypotheses.
    Status moves from GENERATED → PENDING_REVIEW → ACCEPTED | REJECTED | SUPERSEDED
    only via an authenticated officer action.
    """
    __tablename__ = "hypotheses"

    # ── Identity ──────────────────────────────────────────────────────────────
    hypothesis_id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # ── Claim ─────────────────────────────────────────────────────────────────
    claim: Mapped[str] = mapped_column(String(500), nullable=False)
    # Human-readable, e.g.:
    # "Person P-17 travelled in Vehicle V-4521 from Camera A to Camera C (18:00–18:20)"

    hypothesis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. PERSON_VEHICLE_ASSOCIATION | VEHICLE_SWITCH | TRAJECTORY_LINK |
    #       GROUP_MEMBERSHIP | CONVOY

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # 0.0 – 1.0
    confidence_band: Mapped[str] = mapped_column(String(20), nullable=False)
    # LOW | MEDIUM | HIGH | VERY_HIGH

    scoring_maturity: Mapped[str] = mapped_column(String(30), nullable=False, default="mvp_partial")
    # e.g., mvp_partial | calibrated
    
    scoring_method: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    # e.g., weighted_heuristic_v1 | naive_average_fallback

    # ── Supporting evidence (JSON arrays of IDs) ──────────────────────────────
    supporting_observations: Mapped[Optional[list]] = mapped_column(JSON)
    supporting_interactions: Mapped[Optional[list]] = mapped_column(JSON)
    # IDs of InteractionEvent rows that support this hypothesis

    # ── Explainability ────────────────────────────────────────────────────────
    reason_codes: Mapped[Optional[list]] = mapped_column(JSON)
    contributing_factors: Mapped[Optional[list]] = mapped_column(JSON)
    # [{factor, weight, value}, ...]

    # ── Competing hypotheses ──────────────────────────────────────────────────
    alternative_hypotheses: Mapped[Optional[list]] = mapped_column(JSON)
    # IDs of other Hypothesis rows that are mutually exclusive with this one

    # ── Status (v4.1 §25) ─────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="GENERATED")
    # GENERATED | PENDING_REVIEW | ACCEPTED | REJECTED | SUPERSEDED

    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Officer review fields ─────────────────────────────────────────────────
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(50))       # user_id
    review_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_decision: Mapped[Optional[str]] = mapped_column(String(20))   # ACCEPTED | REJECTED | DEFERRED
    review_notes: Mapped[Optional[str]] = mapped_column(String(1000))

    # ── Primary entity this hypothesis is about ───────────────────────────────
    primary_entity_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    primary_entity_type: Mapped[Optional[str]] = mapped_column(String(20))

    # ── Model metadata ────────────────────────────────────────────────────────
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_hyp_entity_status", "primary_entity_id", "status"),
        Index("ix_hyp_confidence", "confidence_band", "status"),
    )
