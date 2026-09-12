"""
Regression Tests — Real DB Execution Path

Tests the actual SQLite/SQLAlchemy path for bug regressions fixed in v4.1.

1. test_regression_end_time_stamped_on_exit:
   Protects against the bug where RIDING_IN events were left open (end_time=NULL)
   even after EXITED events were processed, because _persist_event didn't close them.

2. test_regression_vehicle_root_query_returns_passenger_events:
   Protects against the bug where querying a vehicle's interaction history
   returned empty results because the query only checked subject_entity_id,
   missing the fact that passengers are subjects and vehicles are objects.
"""

from __future__ import annotations

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models.interaction import InteractionEvent
from database import Base
from engine.interaction import PersonVehicleStateMachine, EntityObservation, get_interaction_engine
from engine.graph import TemporalInvestigationGraph


# Setup in-memory SQLite DB
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def t(offset_seconds: int) -> datetime:
    return datetime(2026, 8, 19, 18, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)


def obs(entity_id: str, etype: str, bbox: list[int], ts_offset: int) -> EntityObservation:
    return EntityObservation(
        entity_id=entity_id,
        entity_type=etype,
        observation_id=f"OBS-{entity_id}-{ts_offset}",
        camera_id="CAM-001",
        timestamp=t(ts_offset),
        bbox=bbox,
        confidence=0.90,
    )


async def test_regression_end_time_stamped_on_exit():
    print("\n─── Test A: Regression - end_time stamped on EXITED ───")
    await init_db()
    async with TestingSessionLocal() as session:
        ie = get_interaction_engine()
        ie._pv_machines.clear()  # reset singleton state

        # BBoxes
        V_BOX = [100, 200, 400, 500]
        P_ENTER = [120, 220, 380, 490]
        P_AWAY = [1100, 50, 1150, 150]

        # 1. Drive to RIDING_IN
        await ie.process_co_observation(obs("P-99", "PERSON", P_ENTER, 0), obs("V-88", "VEHICLE", V_BOX, 0), session) # PROXIMITY
        await ie.process_co_observation(obs("P-99", "PERSON", P_ENTER, 2), obs("V-88", "VEHICLE", V_BOX, 2), session) # ENTRY
        await ie.process_co_observation(obs("P-99", "PERSON", P_ENTER, 4), obs("V-88", "VEHICLE", V_BOX, 4), session) # ENTERED
        events_riding = await ie.process_co_observation(obs("P-99", "PERSON", P_ENTER, 6), obs("V-88", "VEHICLE", V_BOX, 6), session) # RIDING_IN

        assert len(events_riding) == 1
        riding_event = events_riding[0]
        assert riding_event.event_type == "RIDING_IN"
        assert riding_event.end_time is None, "RIDING_IN should start with end_time=None"

        # 2. Drive to EXITED (terminal state)
        # Note: POSSIBLE_EXIT is the first terminal state, so it closes the RIDING_IN event.
        events_poss = await ie.process_co_observation(obs("P-99", "PERSON", P_AWAY, 100), obs("V-88", "VEHICLE", V_BOX, 100), session) # POSSIBLE_EXIT
        events_exited = await ie.process_co_observation(obs("P-99", "PERSON", P_AWAY, 102), obs("V-88", "VEHICLE", V_BOX, 102), session) # EXITED

        assert len(events_exited) == 1
        exited_event = events_exited[0]
        poss_event = events_poss[0]
        assert exited_event.event_type == "EXITED"

        # 3. Refresh the riding event from DB to verify its end_time was back-filled
        await session.refresh(riding_event)
        
        # EXACT REGRESSION ASSERTION
        assert riding_event.end_time is not None, "BUG REGRESSION: RIDING_IN event was left with end_time=NULL after EXITED"
        assert riding_event.end_time == exited_event.start_time, "BUG REGRESSION: RIDING_IN end_time should close on confirmed EXITED, not tentative POSSIBLE_EXIT"
        print("✅ Regression test A passed: end_time correctly back-filled via DB.")


async def test_regression_vehicle_root_query_returns_passenger_events():
    print("\n─── Test B: Regression - Vehicle root queries passenger edges ───")
    await init_db()
    async with TestingSessionLocal() as session:
        # 1. Manually persist a relationship where Vehicle is the OBJECT
        ev = InteractionEvent(
            event_id="IE-REG-1",
            event_type="RIDING_IN",
            interaction_class="PERSON_VEHICLE",
            subject_entity_id="P-101",
            subject_entity_type="PERSON",
            object_entity_id="V-202",
            object_entity_type="VEHICLE",
            camera_id="CAM-001",
            start_time=t(0),
            confidence=0.95,
            generic_lifecycle="ACTIVE",
            domain_state_before="ENTERED",
            domain_state_after="RIDING_IN",
            model_version="test"
        )
        session.add(ev)
        await session.commit()

        # 2. Use TemporalInvestigationGraph with Vehicle as the Root
        g = TemporalInvestigationGraph()
        # EXACT REGRESSION METHOD CALL
        events = await g._fetch_events_for_entity("V-202", session)
        
        # EXACT REGRESSION ASSERTION
        assert len(events) == 1, "BUG REGRESSION: _fetch_events_for_entity returned 0 events for Vehicle root (missing OR clause)"
        assert events[0].subject_entity_id == "P-101"
        assert events[0].object_entity_id == "V-202"

        # Further verify graph expansion works (Fix 2b)
        await g.build_for_entity("V-202", "VEHICLE", session, depth=1)
        assert g.graph.has_node("P-101"), "BUG REGRESSION: passenger node not discovered when expanding from vehicle root"
        
        print("✅ Regression test B passed: Vehicle root correctly resolves passenger edges.")


async def test_regression_false_alarm_does_not_split_riding_in():
    """
    Regression test for: POSSIBLE_EXIT → RIDING_IN (false alarm) must NOT
    leave a closed/orphaned RIDING_IN event behind. The ride should appear
    as one continuous interval, not two intervals with a false gap.
    """
    print("\n─── Test C: Regression - false alarm does not fragment RIDING_IN ───")
    await init_db()
    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        ie = get_interaction_engine()
        ie._pv_machines.clear()

        V_BOX = [100, 200, 400, 500]
        P_ENTER = [120, 220, 380, 490]
        P_BLIP = [900, 50, 950, 150]   # momentary drop in proximity — not a real exit

        # 1. Drive to RIDING_IN
        await ie.process_co_observation(obs("P-77", "PERSON", P_ENTER, 0), obs("V-66", "VEHICLE", V_BOX, 0), session)
        await ie.process_co_observation(obs("P-77", "PERSON", P_ENTER, 2), obs("V-66", "VEHICLE", V_BOX, 2), session)
        await ie.process_co_observation(obs("P-77", "PERSON", P_ENTER, 4), obs("V-66", "VEHICLE", V_BOX, 4), session)
        events_riding = await ie.process_co_observation(obs("P-77", "PERSON", P_ENTER, 6), obs("V-66", "VEHICLE", V_BOX, 6), session)
        riding_event = events_riding[0]
        assert riding_event.event_type == "RIDING_IN"

        # 2. Momentary blip → POSSIBLE_EXIT
        events_blip = await ie.process_co_observation(obs("P-77", "PERSON", P_BLIP, 50), obs("V-66", "VEHICLE", V_BOX, 50), session)
        assert len(events_blip) == 1
        assert events_blip[0].domain_state_after == "POSSIBLE_EXIT", "Debug: P_BLIP did not trigger POSSIBLE_EXIT"

        # 3. False alarm resolves → back to RIDING_IN (overlap recovers)
        #    With the fix, _persist_event returns None and the caller returns [],
        #    so events_created should be 0 — no new row, no stale row returned.
        events_resolve = await ie.process_co_observation(obs("P-77", "PERSON", P_ENTER, 52), obs("V-66", "VEHICLE", V_BOX, 52), session)
        assert len(events_resolve) == 0, (
            "BUG REGRESSION: false-alarm reversion should produce events_created=0, "
            f"got {len(events_resolve)}"
        )

        # 4. Refresh the original riding event
        await session.refresh(riding_event)

        # EXACT REGRESSION ASSERTION
        assert riding_event.end_time is None, (
            "BUG REGRESSION: false-alarm POSSIBLE_EXIT closed the RIDING_IN "
            "event even though the person never actually exited."
        )

        # Confirm no phantom "gap" event was left with a stale end_time
        all_events = await session.execute(
            select(InteractionEvent).where(
                InteractionEvent.subject_entity_id == "P-77",
                InteractionEvent.object_entity_id == "V-66",
            )
        )
        riding_rows = [e for e in all_events.scalars() if e.event_type == "RIDING_IN"]
        assert len(riding_rows) == 1, (
            f"BUG REGRESSION: expected 1 continuous RIDING_IN event, "
            f"found {len(riding_rows)} — false alarm fragmented the interval."
        )

        print("✅ Regression test C passed: false alarm did not fragment RIDING_IN.")


async def test_regression_real_reentry_creates_new_ride():
    """
    Regression test for: after a CONFIRMED exit (EXITED), a genuine
    second ride into the same vehicle must create a NEW InteractionEvent,
    not get merged into the first via the false-alarm dedup logic.
    """
    print("\n─── Test D: Regression - real re-entry creates a new ride ───")
    await init_db()
    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        ie = get_interaction_engine()
        ie._pv_machines.clear()

        V_BOX = [100, 200, 400, 500]
        P_ENTER = [120, 220, 380, 490]
        P_AWAY = [1100, 50, 1150, 150]

        # 1. First ride: full sequence to confirmed EXITED
        await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 0), obs("V-44", "VEHICLE", V_BOX, 0), session)
        await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 2), obs("V-44", "VEHICLE", V_BOX, 2), session)
        await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 4), obs("V-44", "VEHICLE", V_BOX, 4), session)
        events_riding_1 = await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 6), obs("V-44", "VEHICLE", V_BOX, 6), session)
        riding_event_1 = events_riding_1[0]

        await ie.process_co_observation(obs("P-55", "PERSON", P_AWAY, 100), obs("V-44", "VEHICLE", V_BOX, 100), session)  # POSSIBLE_EXIT
        events_exited = await ie.process_co_observation(obs("P-55", "PERSON", P_AWAY, 102), obs("V-44", "VEHICLE", V_BOX, 102), session)  # EXITED
        exited_event = events_exited[0]
        assert exited_event.event_type == "EXITED"

        await session.refresh(riding_event_1)
        assert riding_event_1.end_time == exited_event.start_time, "First ride should be closed on confirmed EXITED"

        # 2. Second, genuine ride: full sequence again, same pair, later time
        ie._pv_machines.clear()  # simulate a fresh proximity detection cycle
        await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 200), obs("V-44", "VEHICLE", V_BOX, 200), session)
        await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 202), obs("V-44", "VEHICLE", V_BOX, 202), session)
        await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 204), obs("V-44", "VEHICLE", V_BOX, 204), session)
        events_riding_2 = await ie.process_co_observation(obs("P-55", "PERSON", P_ENTER, 206), obs("V-44", "VEHICLE", V_BOX, 206), session)

        # EXACT REGRESSION ASSERTIONS
        assert len(events_riding_2) == 1, "BUG REGRESSION: real re-entry did not create a new event (events_created should be 1, not 0)"
        riding_event_2 = events_riding_2[0]
        assert riding_event_2.event_id != riding_event_1.event_id, "BUG REGRESSION: second ride was merged into the first ride's row"
        assert riding_event_2.end_time is None, "Second ride should start open"

        # 3. Confirm both rows exist independently in the DB
        all_events = await session.execute(
            select(InteractionEvent).where(
                InteractionEvent.subject_entity_id == "P-55",
                InteractionEvent.object_entity_id == "V-44",
                InteractionEvent.event_type == "RIDING_IN",
            )
        )
        riding_rows = list(all_events.scalars())
        assert len(riding_rows) == 2, f"BUG REGRESSION: expected 2 independent rides, found {len(riding_rows)}"

        print("✅ Regression test D passed: real re-entry created a new, independent ride.")


if __name__ == "__main__":
    asyncio.run(test_regression_end_time_stamped_on_exit())
    asyncio.run(test_regression_vehicle_root_query_returns_passenger_events())
    asyncio.run(test_regression_false_alarm_does_not_split_riding_in())
    asyncio.run(test_regression_real_reentry_creates_new_ride())
    print("\n✅ All DB regression tests passed.")
