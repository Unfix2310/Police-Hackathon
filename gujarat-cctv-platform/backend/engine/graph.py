"""
Temporal Investigation Graph — v4.1 §20, §23

Replaces the previous static nx.Graph() with a directed, temporal graph
where every edge carries start_time, end_time, confidence, and evidence_refs.

Architecture rule (v4.1 §27):
    Input contract:  InteractionEvent rows from the interaction_events table
    Output contract: Graph serialised as {nodes, edges} with temporal metadata

Key difference from v3 graph.py:
    STATIC (old):    P-17 ──── V-4521   (just a link)
    TEMPORAL (v4.1): P-17 ──RIDING_IN──▶ V-4521
                          start: 18:00  end: 18:20  conf: 0.92  evidence: [IE-001]

Supported queries (§23):
    1. "Who was inside V-4521 at 18:15?" → active RIDING_IN edges at that time
    2. "Where did P-17 go after V-4521?"  → all edges after EXITED event
    3. "What vehicles has P-17 used?"     → all RIDING_IN edges for P-17
    4. "Did V-4521 and V-4521b share a passenger?" → graph path analysis
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.interaction import InteractionEvent, Hypothesis
from models.enums import PersonVehicleDomainState, HypothesisStatus

logger = logging.getLogger("cctv_platform.graph")


class TemporalInvestigationGraph:
    """
    v4.1 §20 — Temporal Investigation Graph.

    Uses nx.MultiDiGraph so that:
    - Edges are directed (subject → object)
    - Multiple edges can exist between the same pair (e.g. person used same vehicle twice)
    - Each edge carries full temporal metadata and evidence provenance
    """

    def __init__(self):
        # MultiDiGraph: directed, allows parallel edges with different timestamps
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()

    # ── Build / refresh ──────────────────────────────────────────────────

    async def build_for_entity(
        self,
        entity_id: str,
        entity_type: str,
        db: AsyncSession,
        depth: int = 2,
    ) -> "TemporalInvestigationGraph":
        """
        Build a temporal graph centred on entity_id, traversing up to `depth`
        hops through InteractionEvent edges.

        Each hop adds the directly connected entities and all their shared events.
        Returns self for chaining.
        """
        self.graph.clear()
        visited: set = set()
        frontier = {entity_id}
        current_type_map = {entity_id: entity_type}

        for _hop in range(depth):
            if not frontier:
                break
            next_frontier: set = set()

            for eid in frontier:
                if eid in visited:
                    continue
                visited.add(eid)
                etype = current_type_map.get(eid, "UNKNOWN")

                # Add node
                self.graph.add_node(
                    eid,
                    entity_type=etype,
                    is_root=(eid == entity_id),
                )

                # Fetch all events where this entity is subject OR object
                events = await self._fetch_events_for_entity(eid, db)
                for ev in events:
                    self._add_edge(ev)

                    # Discover connected entities for next hop — both directions
                    # When eid is subject, discover the object peer.
                    # When eid is object, discover the subject peer.
                    peer = (
                        ev.object_entity_id
                        if ev.subject_entity_id == eid
                        else ev.subject_entity_id
                    )
                    peer_type = (
                        ev.object_entity_type or "UNKNOWN"
                        if ev.subject_entity_id == eid
                        else ev.subject_entity_type or "UNKNOWN"
                    )
                    if peer and peer not in visited:
                        next_frontier.add(peer)
                        current_type_map[peer] = peer_type
                        if not self.graph.has_node(peer):
                            self.graph.add_node(
                                peer,
                                entity_type=peer_type,
                                is_root=False,
                            )

            frontier = next_frontier

        logger.debug(
            "Graph built for %s: %d nodes, %d edges",
            entity_id, self.graph.number_of_nodes(), self.graph.number_of_edges(),
        )
        return self

    # ── Temporal queries (§23) ───────────────────────────────────────────

    def who_was_in_vehicle_at(
        self, vehicle_id: str, at_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Query 1: Who was inside vehicle_id at time at_time?
        Returns list of {entity_id, confidence, edge_key} for all RIDING_IN
        edges that were active at the given timestamp.
        """
        results = []
        for src, tgt, key, data in self.graph.edges(data=True, keys=True):
            if tgt != vehicle_id:
                continue
            if data.get("edge_type") not in ("RIDING_IN", "ENTERED"):
                continue
            start = data.get("start_time")
            end = data.get("end_time")
            if start and start <= at_time and (end is None or end >= at_time):
                results.append({
                    "entity_id": src,
                    "entity_type": self.graph.nodes[src].get("entity_type"),
                    "confidence": data.get("confidence"),
                    "edge_type": data.get("edge_type"),
                    "start_time": start,
                    "end_time": end,
                })
        return results

    def get_entity_vehicles(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Query 3: All vehicles a person has been associated with.
        Returns list of {vehicle_id, edge_type, start_time, end_time, confidence}.
        """
        results = []
        for src, tgt, data in self.graph.out_edges(entity_id, data=True):
            if data.get("edge_type") in ("ENTERED", "RIDING_IN", "EXITED"):
                results.append({
                    "vehicle_id": tgt,
                    "edge_type": data.get("edge_type"),
                    "start_time": data.get("start_time"),
                    "end_time": data.get("end_time"),
                    "confidence": data.get("confidence"),
                    "evidence_refs": data.get("evidence_refs", []),
                })
        results.sort(key=lambda r: r["start_time"] or datetime.min)
        return results

    def shared_passengers(
        self, vehicle_a_id: str, vehicle_b_id: str
    ) -> List[str]:
        """
        Query 4: Did vehicle_a and vehicle_b ever share a passenger?
        Returns list of entity_ids that have RIDING_IN edges to both vehicles.
        """
        passengers_a = {
            src for src, tgt, data in self.graph.edges(data=True)
            if tgt == vehicle_a_id and data.get("edge_type") in ("RIDING_IN", "ENTERED")
        }
        passengers_b = {
            src for src, tgt, data in self.graph.edges(data=True)
            if tgt == vehicle_b_id and data.get("edge_type") in ("RIDING_IN", "ENTERED")
        }
        return list(passengers_a & passengers_b)

    def get_entity_timeline(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Returns all edges for an entity sorted by start_time — the entity's
        complete relationship timeline. Powers the Investigator timeline view.
        """
        events = []
        for src, tgt, data in self.graph.out_edges(entity_id, data=True):
            events.append({
                "subject_id":   src,
                "object_id":    tgt,
                "object_type":  self.graph.nodes[tgt].get("entity_type") if self.graph.has_node(tgt) else "UNKNOWN",
                "edge_type":    data.get("edge_type"),
                "start_time":   data.get("start_time"),
                "end_time":     data.get("end_time"),
                "confidence":   data.get("confidence"),
                "evidence_refs": data.get("evidence_refs", []),
                "reason_codes": data.get("reason_codes", []),
                "camera_id":    data.get("camera_id"),
            })
        events.sort(key=lambda e: e["start_time"] or datetime.min)
        return events

    def find_path(
        self, source_id: str, target_id: str
    ) -> List[str]:
        """
        Find the shortest entity path between source and target.
        Uses an undirected view of the graph for path searching.
        """
        try:
            return nx.shortest_path(self.graph.to_undirected(), source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    # ── Serialisation ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Serialise to {nodes, edges} for the frontend investigation graph view.
        All datetime values are ISO-8601 strings.
        """
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id":          node_id,
                "entity_type": attrs.get("entity_type", "UNKNOWN"),
                "is_root":     attrs.get("is_root", False),
            })

        edges = []
        for src, tgt, key, data in self.graph.edges(data=True, keys=True):
            edges.append({
                "source":       src,
                "target":       tgt,
                "edge_key":     key,
                "edge_type":    data.get("edge_type"),
                "start_time":   _isoformat(data.get("start_time")),
                "end_time":     _isoformat(data.get("end_time")),
                "confidence":   data.get("confidence"),
                "camera_id":    data.get("camera_id"),
                "evidence_refs": data.get("evidence_refs", []),
                "reason_codes": data.get("reason_codes", []),
                "generic_lifecycle": data.get("generic_lifecycle"),
                "domain_state": data.get("domain_state_after"),
            })

        return {"nodes": nodes, "edges": edges}

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _fetch_events_for_entity(
        self, entity_id: str, db: AsyncSession
    ) -> List[InteractionEvent]:
        """
        Fetch all events where entity_id is subject OR object.

        Fix 2: the original query only fetched subject_entity_id == entity_id.
        A vehicle root would produce an empty graph because passengers (persons)
        are always the *subject* and vehicles the *object*.
        The OR clause ensures both directions are captured for any entity type.
        """
        from sqlalchemy import or_ as sql_or
        result = await db.execute(
            select(InteractionEvent).where(
                sql_or(
                    InteractionEvent.subject_entity_id == entity_id,
                    InteractionEvent.object_entity_id == entity_id,
                )
            ).order_by(InteractionEvent.start_time)
        )
        return list(result.scalars().all())


    def _add_edge(self, ev: InteractionEvent) -> None:
        """Add a single InteractionEvent as a directed temporal edge."""
        if not ev.object_entity_id:
            return

        # Ensure both nodes exist
        if not self.graph.has_node(ev.subject_entity_id):
            self.graph.add_node(
                ev.subject_entity_id,
                entity_type=ev.subject_entity_type,
                is_root=False,
            )
        if not self.graph.has_node(ev.object_entity_id):
            self.graph.add_node(
                ev.object_entity_id,
                entity_type=ev.object_entity_type or "UNKNOWN",
                is_root=False,
            )

        # Add directed temporal edge
        self.graph.add_edge(
            ev.subject_entity_id,
            ev.object_entity_id,
            key=ev.event_id,                     # unique key per event
            edge_type=ev.event_type,
            start_time=ev.start_time,
            end_time=ev.end_time,
            confidence=ev.confidence,
            generic_lifecycle=ev.generic_lifecycle,
            domain_state_before=ev.domain_state_before,
            domain_state_after=ev.domain_state_after,
            camera_id=ev.camera_id,
            evidence_refs=ev.evidence_obs_ids or [],
            reason_codes=ev.reason_codes or [],
            event_id=ev.event_id,
        )


# ── Utility ───────────────────────────────────────────────────────────────────

def _isoformat(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ── Module-level singleton ────────────────────────────────────────────────────

def new_temporal_graph() -> TemporalInvestigationGraph:
    """
    Returns a fresh TemporalInvestigationGraph instance.
    A new instance is created per investigation request so graphs
    don't bleed across requests.
    """
    return TemporalInvestigationGraph()
