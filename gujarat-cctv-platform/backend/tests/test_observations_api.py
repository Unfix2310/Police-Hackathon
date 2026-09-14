import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi import HTTPException
from database import Base
from models.camera import Camera
from models.observation import Observation
from models.enums import ObservationType
from api.observations import search_observations, get_observation, create_observation
from engine.entity_resolver import EntityResolver
from config import settings

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def t(offset_seconds: int) -> datetime:
    return datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)

async def test_observations_api_lifecycle():
    print("\n─── 1. Observations API: Real DB CRUD & Filtering ───")
    await init_test_db()
    
    async with TestingSessionLocal() as db:
        # Seed test camera
        cam = Camera(
            cam_id="CAM-GJ-AHM-SG-001",
            display_name="SG Highway Junction 1",
            jurisdiction_code="GJ-AHM",
            latitude=23.0338,
            longitude=72.5256
        )
        cam2 = Camera(
            cam_id="CAM-GJ-AHM-SG-002",
            display_name="SG Highway Junction 2 (Distant)",
            jurisdiction_code="GJ-AHM",
            latitude=23.1000,
            longitude=72.6000
        )
        db.add_all([cam, cam2])
        await db.commit()

        # Step 1: POST /observations
        post_payload = {
            "source_camera_id": "CAM-GJ-AHM-SG-001",
            "observation_type": "VEHICLE",
            "timestamp_capture": t(100).isoformat(),
            "bounding_box": [120, 200, 350, 450],
            "confidence": 0.94,
            "payload": {
                "plate_text": "GJ01AB1234",
                "color": "White",
                "type": "Sedan"
            }
        }
        res_post = await create_observation(payload=post_payload, db=db, user={"role": "investigator"})
        assert "observation_id" in res_post
        obs_id = res_post["observation_id"]
        assert res_post["status"] == "created"
        print(f"✅ POST /observations succeeded: created ID {obs_id}")

        # Step 2: GET /observations/{obs_id}
        res_get = await get_observation(obs_id=obs_id, db=db, user={"role": "investigator"})
        assert res_get["observation_id"] == obs_id
        assert res_get["source_camera_id"] == "CAM-GJ-AHM-SG-001"
        assert res_get["camera_name"] == "SG Highway Junction 1"
        assert res_get["payload"]["plate_text"] == "GJ01AB1234"
        print(f"✅ GET /observations/{obs_id} returned full canonical payload.")

        # Step 3: GET /observations/{non_existent} -> 404
        try:
            await get_observation(obs_id="obs-does-not-exist-9999", db=db, user={"role": "investigator"})
            assert False, "Expected HTTPException 404 for missing observation!"
        except HTTPException as exc:
            assert exc.status_code == 404
            print("✅ GET /observations/{non_existent} correctly returned 404 Not Found.")

        # Step 4: GET /observations with filters
        # A. Filter by camera_id
        res_filter_cam = await search_observations(
            start_time=None, end_time=None, camera_id="CAM-GJ-AHM-SG-001",
            type=None, lat=None, lon=None, radius_meters=None,
            db=db, user={"role": "investigator"}
        )
        assert res_filter_cam["total"] == 1
        assert res_filter_cam["observations"][0]["observation_id"] == obs_id
        print("✅ GET /observations filtered by camera_id returned matching row.")

        # B. Filter by time window (in range)
        res_filter_time = await search_observations(
            start_time=t(50).isoformat(), end_time=t(150).isoformat(),
            camera_id=None, type=None, lat=None, lon=None, radius_meters=None,
            db=db, user={"role": "investigator"}
        )
        assert res_filter_time["total"] == 1

        # C. Filter by time window (out of range)
        res_filter_out_time = await search_observations(
            start_time=t(200).isoformat(), end_time=t(300).isoformat(),
            camera_id=None, type=None, lat=None, lon=None, radius_meters=None,
            db=db, user={"role": "investigator"}
        )
        assert res_filter_out_time["total"] == 0
        print("✅ GET /observations temporal filtering verified.")

        # D. Spatial filter with Haversine radius
        # Point near CAM-GJ-AHM-SG-001 (lat=23.0338, lon=72.5256): within 500m
        res_spatial_hit = await search_observations(
            start_time=None, end_time=None, camera_id=None, type=None,
            lat=23.0339, lon=72.5257, radius_meters=500,
            db=db, user={"role": "investigator"}
        )
        assert res_spatial_hit["total"] == 1
        assert res_spatial_hit["observations"][0]["observation_id"] == obs_id

        # Point far away: radius 500m from (23.50, 73.00)
        res_spatial_miss = await search_observations(
            start_time=None, end_time=None, camera_id=None, type=None,
            lat=23.5000, lon=73.0000, radius_meters=500,
            db=db, user={"role": "investigator"}
        )
        assert res_spatial_miss["total"] == 0
        print("✅ GET /observations Haversine spatial radius filtering verified.")

async def test_pedestrian_speed_gate_calibration():
    print("\n─── 2. Pedestrian 20 km/h Speed Gate Calibration Verification ───")
    await init_test_db()
    async with TestingSessionLocal() as db:
        resolver = EntityResolver()

        # Seed person on cam05 at t(0)
        res1 = await resolver.resolve_person(
            obs_id="OBS-PED-1",
            timestamp=t(0),
            camera_id="cam05",
            clothing_color="black",
            confidence=0.90,
            db=db
        )
        pid = res1["entity_id"]

        obs1 = Observation(
            observation_id="OBS-PED-1",
            source_camera_id="cam05",
            timestamp_capture=t(0),
            bounding_box=[50, 50, 150, 200],
            confidence=0.90,
            observation_type=ObservationType.PERSON
        )
        db.add(obs1)
        await db.commit()

        # Plausible foot transit: 228m in 90 seconds (~9.1 km/h <= 20 km/h) -> should associate
        res2 = await resolver.resolve_person(
            obs_id="OBS-PED-2",
            timestamp=t(90),
            camera_id="cam16", # 228m away
            clothing_color="black",
            confidence=0.90,
            db=db
        )
        assert res2["is_new"] is False
        assert res2["entity_id"] == pid
        print("✅ Plausible pedestrian pace (9.1 km/h <= 20.0 km/h) successfully associated.")

        # Implausible foot transit: 228m in 15 seconds = 0.228 km / (15/3600 h) = 54.7 km/h > 20 km/h
        # Must be rejected by the 20 km/h speed gate!
        res3 = await resolver.resolve_person(
            obs_id="OBS-PED-3",
            timestamp=t(15), # 15s after cam05
            camera_id="cam16",
            clothing_color="black",
            confidence=0.90,
            db=db
        )
        assert res3["is_new"] is True, "Implausible foot transit (54.7 km/h) was wrongly merged!"
        assert res3["entity_id"] != pid
        print("✅ Implausible pedestrian speed (54.7 km/h > 20.0 km/h) successfully rejected.")

async def main():
    await test_observations_api_lifecycle()
    await test_pedestrian_speed_gate_calibration()
    print("\n🎉 All observations API and speed gate tests PASSED successfully!\n")

if __name__ == "__main__":
    asyncio.run(main())
