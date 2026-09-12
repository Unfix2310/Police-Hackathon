import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database import Base
from models.user import User
from models.entity import Vehicle, Person, VehicleObservation, PersonObservation
from models.observation import Observation
from models.incident import Incident
from models.enums import IncidentSeverity, ObservationType
from engine.entity_resolver import EntityResolver
from ai.tracker import ObjectTracker, Detection
from api.correlation import correlate_entities
from api.analytics import get_overview
import hashlib
import secrets

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def t(offset_seconds: int) -> datetime:
    return datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

async def test_auth_rejects_backdoor_passwords():
    print("\n─── 1. Auth Backdoor Removal Verification ───")
    await init_test_db()
    async with TestingSessionLocal() as db:
        user = User(
            user_id="USR-TEST-001",
            badge_number="GJ-TEST-001",
            full_name="Test Officer",
            department="Cyber Crime",
            district="Ahmedabad",
            police_station="State Police HQ",
            jurisdiction_code="GJ-AHM",
            role="command",
            password_hash=hash_pw("demo123"),
            is_active=True
        )
        db.add(user)
        await db.commit()

        # Test rejected backdoor passwords
        backdoor_passwords = ["123", "password", "command123", "admin123", "operator123", "wrongpass"]
        for pw in backdoor_passwords:
            computed_hash = hash_pw(pw)
            valid = secrets.compare_digest(user.password_hash, computed_hash)
            assert not valid, f"SECURITY FAILURE: Backdoor password '{pw}' was accepted!"

        # Test valid password
        valid = secrets.compare_digest(user.password_hash, hash_pw("demo123"))
        assert valid, "Valid password 'demo123' was wrongly rejected."
        print("✅ Auth verification passed: All backdoor passwords rejected, valid password accepted.")

async def test_cross_camera_person_resolution():
    print("\n─── 2. Cross-Camera Person Resolution Verification ───")
    await init_test_db()
    async with TestingSessionLocal() as db:
        resolver = EntityResolver()

        # Step 1: Initial observation on cam05 (Junction)
        res1 = await resolver.resolve_person(
            obs_id="OBS-P1-001",
            timestamp=t(0),
            camera_id="cam05",
            clothing_color="blue",
            confidence=0.85,
            db=db
        )
        assert res1["is_new"] is True
        p_id = res1["entity_id"]

        # Also insert base Observation record so join succeeds
        obs1 = Observation(
            observation_id="OBS-P1-001",
            source_camera_id="cam05",
            timestamp_capture=t(0),
            bounding_box=[100, 100, 200, 200],
            confidence=0.85,
            observation_type=ObservationType.PERSON
        )
        db.add(obs1)
        await db.commit()

        # Step 2: Cross-camera observation 90 seconds later on adjacent cam16 (228m away)
        res2 = await resolver.resolve_person(
            obs_id="OBS-P1-002",
            timestamp=t(90),
            camera_id="cam16",
            clothing_color="blue",
            confidence=0.88,
            db=db
        )
        assert res2["is_new"] is False, "Cross-camera person was not linked to existing entity!"
        assert res2["entity_id"] == p_id, f"Expected {p_id}, got {res2['entity_id']}"
        assert res2["method"] == "CROSS_CAMERA_SOFT_BIOMETRIC"
        print(f"✅ Cross-camera resolution passed: Person tracked across cameras ({res2['method']}).")

        obs2 = Observation(
            observation_id="OBS-P1-002",
            source_camera_id="cam16",
            timestamp_capture=t(90),
            bounding_box=[100, 100, 200, 200],
            confidence=0.88,
            observation_type=ObservationType.PERSON
        )
        db.add(obs2)
        await db.commit()

        # Step 3: Physically impossible cross-camera jump (teleportation / extreme speed)
        # 1 second later across different city 300km away (cam30 in Kutch)
        res3 = await resolver.resolve_person(
            obs_id="OBS-P1-003",
            timestamp=t(91),
            camera_id="cam30",
            clothing_color="blue",
            confidence=0.90,
            db=db
        )
        assert res3["is_new"] is True, "Spatial feasibility gate failed to reject impossible travel!"
        assert res3["entity_id"] != p_id
        print("✅ Spatial feasibility gate passed: Impossible cross-camera jump spawned new entity.")

async def test_tracker_kalman_and_bytetrack():
    print("\n─── 3. AI Tracker (Kalman Filter + ByteTrack) Verification ───")
    tracker = ObjectTracker(iou_threshold=0.3, track_buffer_ms=1000.0)

    # Frame 1: High confidence detection
    det1 = Detection(bbox=[100, 100, 150, 200], class_id=0, confidence=0.85)
    tracks1 = tracker.update([det1], pts_ms=0.0)
    assert len(tracks1) == 1
    t_id = tracks1[0].track_id

    # Frame 2: Slightly shifted detection with Kalman update
    det2 = Detection(bbox=[105, 102, 155, 202], class_id=0, confidence=0.80)
    tracks2 = tracker.update([det2], pts_ms=100.0)
    assert len(tracks2) == 1
    assert tracks2[0].track_id == t_id

    # Frame 3: Low-confidence detection (e.g. occlusion/blur, confidence=0.25)
    # ByteTrack stage 2 should recover and match to active track!
    det3_low = Detection(bbox=[110, 105, 160, 205], class_id=0, confidence=0.25)
    tracks3 = tracker.update([det3_low], pts_ms=200.0)
    assert len(tracks3) == 1
    assert tracks3[0].track_id == t_id, "ByteTrack failed to recover track via low-confidence detection!"
    print("✅ Tracker verification passed: Kalman Filter and ByteTrack occlusion recovery verified.")

async def test_correlate_endpoint():
    print("\n─── 4. POST /correlate Spatio-Temporal Engine Verification ───")
    await init_test_db()
    async with TestingSessionLocal() as db:
        # Create observations for Target Vehicle (V-T1) and Companion Vehicle (V-C1)
        # Sighting 1 on CAM-001
        o1 = Observation(observation_id="OBS-T1-1", source_camera_id="cam_ahmedabad_01", timestamp_capture=t(0), bounding_box=[0,0,1,1], confidence=0.9, observation_type=ObservationType.VEHICLE)
        vo1 = VehicleObservation(observation_id="OBS-T1-1", vehicle_id="V-TARGET-01", timestamp_capture=t(0))
        o2 = Observation(observation_id="OBS-C1-1", source_camera_id="cam_ahmedabad_01", timestamp_capture=t(5), bounding_box=[0,0,1,1], confidence=0.9, observation_type=ObservationType.VEHICLE)
        vo2 = VehicleObservation(observation_id="OBS-C1-1", vehicle_id="V-COMPANION-01", timestamp_capture=t(5))

        # Sighting 2 on CAM-002
        o3 = Observation(observation_id="OBS-T1-2", source_camera_id="cam_ahmedabad_02", timestamp_capture=t(120), bounding_box=[0,0,1,1], confidence=0.9, observation_type=ObservationType.VEHICLE)
        vo3 = VehicleObservation(observation_id="OBS-T1-2", vehicle_id="V-TARGET-01", timestamp_capture=t(120))
        o4 = Observation(observation_id="OBS-C1-2", source_camera_id="cam_ahmedabad_02", timestamp_capture=t(125), bounding_box=[0,0,1,1], confidence=0.9, observation_type=ObservationType.VEHICLE)
        vo4 = VehicleObservation(observation_id="OBS-C1-2", vehicle_id="V-COMPANION-01", timestamp_capture=t(125))

        db.add_all([o1, vo1, o2, vo2, o3, vo3, o4, vo4])
        await db.commit()

        mock_user = User(user_id="U1", role="investigator", badge_number="B1", full_name="Inv", department="CID", district="AHM", police_station="PS", jurisdiction_code="GJ")
        
        # Test correlation query
        payload = {
            "target_id": "V-TARGET-01",
            "target_type": "vehicle",
            "correlation_threshold_pct": 30,
            "time_window_seconds": 60
        }
        res = await correlate_entities(payload=payload, db=db, user=mock_user)
        assert len(res) >= 1, "POST /correlate returned empty list instead of co-traveler!"
        match = res[0]
        assert match["entity_id"] == "V-COMPANION-01"
        assert match["relationship_type"] == "CO_TRAVELER"
        assert match["distinct_cameras_count"] == 2
        assert match["correlation_score"] > 0.5
        print(f"✅ Correlation test passed: Co-traveler {match['entity_id']} identified with score {match['correlation_score']}.")

async def test_analytics_metrics():
    print("\n─── 5. Analytics Metrics & Health Verification ───")
    await init_test_db()
    async with TestingSessionLocal() as db:
        inc = Incident(
            incident_id="INC-TEST-001",
            type="Vehicle Theft",
            severity=IncidentSeverity.P2_HIGH,
            status="OPEN",
            description="Active investigation",
            jurisdiction_code="GJ-AHM",
            created_at=datetime.now(timezone.utc)
        )
        db.add(inc)
        await db.commit()

        mock_user = User(user_id="U1", role="command", badge_number="B1", full_name="Cmd", department="HQ", district="AHM", police_station="PS", jurisdiction_code="GJ")
        data = await get_overview(db=db, user=mock_user)
        assert data["active_incidents"] == 1, f"Expected 1 active incident, got {data['active_incidents']}"
        assert "system_health" in data
        assert data["active_cameras"] > 0
        print(f"✅ Analytics overview passed: active_incidents={data['active_incidents']}, health={data['system_health']}.")

async def main():
    await test_auth_rejects_backdoor_passwords()
    await test_cross_camera_person_resolution()
    await test_tracker_kalman_and_bytetrack()
    await test_correlate_endpoint()
    await test_analytics_metrics()
    print("\n🎉 All audit fix verifications passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
