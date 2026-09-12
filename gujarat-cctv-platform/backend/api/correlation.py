from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_db
from auth.rbac import require_role
from models.user import User
from models.entity import Vehicle, Person, VehicleObservation, PersonObservation
from models.observation import Observation
from models.camera import Camera
from simulator.camera_registry import get_camera
import math

router = APIRouter(tags=["Correlation"])

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("/trajectory/{entity_type}/{entity_id}")
async def get_trajectory_feasibility(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """Get full trajectory with spatial-temporal feasibility scores."""
    if entity_type == 'vehicle':
        obs_class = VehicleObservation
        id_col = VehicleObservation.vehicle_id
    elif entity_type == 'person':
        obs_class = PersonObservation
        id_col = PersonObservation.person_id
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type")
        
    target_id = entity_id
    # If a raw observation UUID was passed, resolve it to its parent entity
    if not (entity_id.startswith("V-") or entity_id.startswith("P-")):
        lookup_stmt = select(id_col).where(obs_class.observation_id == entity_id).limit(1)
        resolved_id = await db.scalar(lookup_stmt)
        if resolved_id:
            target_id = resolved_id

    query = (
        select(obs_class, Observation, Camera)
        .join(Observation, 
              (obs_class.observation_id == Observation.observation_id) & 
              (obs_class.timestamp_capture == Observation.timestamp_capture))
        .join(Camera, Observation.source_camera_id == Camera.cam_id)
        .where(id_col == target_id)
        .order_by(Observation.timestamp_capture.asc())
    )
    result = await db.execute(query)
    rows = result.all()
    
    trajectory = []
    feasibility_score = 1.0
    anomalies = []
    
    prev_point = None
    
    for _, obs, cam in rows:
        cam_info = get_camera(cam.cam_id)
        if not cam_info:
            continue
            
        point = {
            "camera_id": cam.cam_id,
            "lat": cam_info["lat"],
            "lng": cam_info["lng"],
            "timestamp": obs.timestamp_capture
        }
        
        if prev_point:
            dist_km = haversine(prev_point["lat"], prev_point["lng"], point["lat"], point["lng"])
            time_diff_hours = (point["timestamp"] - prev_point["timestamp"]).total_seconds() / 3600.0
            
            if time_diff_hours > 0:
                speed_kmh = dist_km / time_diff_hours
                point["speed_from_previous"] = speed_kmh
                
                if speed_kmh > 120:
                    feasibility_score *= max(0.1, 120 / speed_kmh)
                    anomalies.append({
                        "type": "speed_anomaly",
                        "between": [prev_point["camera_id"], point["camera_id"]],
                        "calculated_speed": speed_kmh
                    })
            else:
                if dist_km > 0:
                    feasibility_score = 0.0
                    anomalies.append({
                        "type": "teleportation",
                        "between": [prev_point["camera_id"], point["camera_id"]]
                    })
                    
        trajectory.append(point)
        prev_point = point
        
    return {
        "trajectory": trajectory,
        "feasibility_score": feasibility_score if trajectory else 0.0,
        "anomalies": anomalies
    }

@router.post("/correlate")
async def correlate_entities(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator"]))
):
    """
    Find entities correlated in time and space with a target entity (e.g. co-travelers, convoys, companions).
    Analyzes observation co-occurrences across cameras within a temporal tolerance window.
    """
    target_id = payload.get("target_id", "").strip()
    if not target_id:
        raise HTTPException(status_code=400, detail="target_id is required")

    target_type = payload.get("target_type", "").lower().strip()
    if not target_type:
        target_type = "person" if target_id.startswith("P-") else "vehicle"

    thresh_val = float(payload.get("correlation_threshold_pct", 40))
    min_score = thresh_val / 100.0 if thresh_val > 1.0 else thresh_val
    window_sec = float(payload.get("time_window_seconds", 180))  # 3-minute co-travel window
    max_results = int(payload.get("max_results", 20))

    # Resolve target entity if raw observation was passed
    if not (target_id.startswith("V-") or target_id.startswith("P-")):
        if target_type == "vehicle":
            res = await db.scalar(select(VehicleObservation.vehicle_id).where(VehicleObservation.observation_id == target_id).limit(1))
            if res:
                target_id = res
        else:
            res = await db.scalar(select(PersonObservation.person_id).where(PersonObservation.observation_id == target_id).limit(1))
            if res:
                target_id = res

    # 1. Fetch all observations of target entity
    if target_type == "vehicle":
        stmt = (
            select(VehicleObservation.observation_id, Observation.source_camera_id, Observation.timestamp_capture)
            .join(Observation, and_(
                VehicleObservation.observation_id == Observation.observation_id,
                VehicleObservation.timestamp_capture == Observation.timestamp_capture
            ))
            .where(VehicleObservation.vehicle_id == target_id)
            .order_by(Observation.timestamp_capture.asc())
        )
    else:
        stmt = (
            select(PersonObservation.observation_id, Observation.source_camera_id, Observation.timestamp_capture)
            .join(Observation, and_(
                PersonObservation.observation_id == Observation.observation_id,
                PersonObservation.timestamp_capture == Observation.timestamp_capture
            ))
            .where(PersonObservation.person_id == target_id)
            .order_by(Observation.timestamp_capture.asc())
        )

    target_obs = (await db.execute(stmt)).all()
    if not target_obs:
        return []

    total_target_sightings = len(target_obs)
    # Map candidate_entity_id -> dict of tracking stats
    candidates_map = {}

    # 2. For each target observation, find co-occurring observations on the same camera
    for t_obs_id, t_cam, t_ts in target_obs:
        w_start = t_ts - timedelta(seconds=window_sec)
        w_end = t_ts + timedelta(seconds=window_sec)

        # Vehicles co-occurring
        v_stmt = (
            select(VehicleObservation.vehicle_id, VehicleObservation.observation_id, Observation.timestamp_capture)
            .join(Observation, and_(
                VehicleObservation.observation_id == Observation.observation_id,
                VehicleObservation.timestamp_capture == Observation.timestamp_capture
            ))
            .where(Observation.source_camera_id == t_cam)
            .where(Observation.timestamp_capture >= w_start)
            .where(Observation.timestamp_capture <= w_end)
            .where(VehicleObservation.vehicle_id != target_id)
            .limit(30)
        )
        for v_id, v_obs_id, v_ts in (await db.execute(v_stmt)).all():
            if not v_id:
                continue
            entry = candidates_map.setdefault(v_id, {
                "entity_id": v_id,
                "entity_type": "vehicle",
                "shared_cameras": set(),
                "time_deltas": [],
                "evidence_obs": set(),
                "shared_instances": []
            })
            dt = abs((v_ts - t_ts).total_seconds())
            entry["shared_cameras"].add(t_cam)
            entry["time_deltas"].append(dt)
            entry["evidence_obs"].add(t_obs_id)
            entry["evidence_obs"].add(v_obs_id)
            entry["shared_instances"].append({
                "camera_id": t_cam,
                "target_timestamp": t_ts.isoformat(),
                "peer_timestamp": v_ts.isoformat(),
                "delta_seconds": round(dt, 1)
            })

        # Persons co-occurring
        p_stmt = (
            select(PersonObservation.person_id, PersonObservation.observation_id, Observation.timestamp_capture)
            .join(Observation, and_(
                PersonObservation.observation_id == Observation.observation_id,
                PersonObservation.timestamp_capture == Observation.timestamp_capture
            ))
            .where(Observation.source_camera_id == t_cam)
            .where(Observation.timestamp_capture >= w_start)
            .where(Observation.timestamp_capture <= w_end)
            .where(PersonObservation.person_id != target_id)
            .limit(30)
        )
        for p_id, p_obs_id, p_ts in (await db.execute(p_stmt)).all():
            if not p_id:
                continue
            entry = candidates_map.setdefault(p_id, {
                "entity_id": p_id,
                "entity_type": "person",
                "shared_cameras": set(),
                "time_deltas": [],
                "evidence_obs": set(),
                "shared_instances": []
            })
            dt = abs((p_ts - t_ts).total_seconds())
            entry["shared_cameras"].add(t_cam)
            entry["time_deltas"].append(dt)
            entry["evidence_obs"].add(t_obs_id)
            entry["evidence_obs"].add(p_obs_id)
            entry["shared_instances"].append({
                "camera_id": t_cam,
                "target_timestamp": t_ts.isoformat(),
                "peer_timestamp": p_ts.isoformat(),
                "delta_seconds": round(dt, 1)
            })

    # 3. Score and rank candidates
    results = []
    for cand_id, data in candidates_map.items():
        shared_count = len(data["shared_cameras"])
        total_co_sightings = len(data["time_deltas"])
        avg_delta = sum(data["time_deltas"]) / max(total_co_sightings, 1)

        # Proximity score (closer in time = higher)
        time_score = max(0.1, 1.0 - (avg_delta / window_sec))
        # Frequency score (co-travel across multiple sightings/cameras)
        camera_spread = min(1.0, shared_count / max(total_target_sightings, 1))
        # Overall correlation confidence
        conf = round(min(1.0, 0.50 * time_score + 0.35 * camera_spread + 0.15 * min(1.0, total_co_sightings / 2.0)), 3)

        if conf >= min_score:
            rel_type = "CO_TRAVELER" if shared_count >= 2 else "CO_LOCATED"
            results.append({
                "entity_id": cand_id,
                "entity_type": data["entity_type"],
                "correlation_score": conf,
                "shared_sightings_count": total_co_sightings,
                "distinct_cameras_count": shared_count,
                "shared_cameras": list(data["shared_cameras"]),
                "average_time_gap_seconds": round(avg_delta, 1),
                "relationship_type": rel_type,
                "evidence_observations": list(data["evidence_obs"])[:10],
                "shared_instances": data["shared_instances"][:10]
            })

    results.sort(key=lambda x: (x["correlation_score"], x["shared_sightings_count"]), reverse=True)
    return results[:max_results]
