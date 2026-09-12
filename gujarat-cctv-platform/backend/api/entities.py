from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth.rbac import require_role
from models.user import User
from models.entity import Vehicle, Person, VehicleObservation, PersonObservation
from models.observation import Observation
from models.camera import Camera

router = APIRouter(prefix="/entities", tags=["Entities"])

@router.get("/vehicles")
async def search_vehicles(
    plate: Optional[str] = None,
    color: Optional[str] = None,
    type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Search for vehicle entities."""
    query = select(Vehicle)
    if plate:
        query = query.where(Vehicle.plate.ilike(f"%{plate}%"))
    if color:
        query = query.where(Vehicle.color.ilike(f"%{color}%"))
    if type:
        query = query.where(Vehicle.vehicle_class.ilike(f"%{type}%"))
    
    result = await db.execute(query)
    vehicles = result.scalars().all()
    
    return [
        {
            "vehicle_id": v.vehicle_id,
            "plate": v.plate,
            "color": v.color,
            "vehicle_class": v.vehicle_class,
            "first_seen": v.first_seen,
            "last_seen": v.last_seen,
            "observation_count": v.observation_count
        } for v in vehicles
    ]

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get unified vehicle entity details."""
    result = await db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.get("/vehicles/{vehicle_id}/trajectory")
async def get_vehicle_trajectory(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get spatial trajectory of a vehicle."""
    from simulator.camera_registry import get_camera
    
    query = (
        select(VehicleObservation, Observation, Camera)
        .join(Observation, 
              (VehicleObservation.observation_id == Observation.observation_id) & 
              (VehicleObservation.timestamp_capture == Observation.timestamp_capture))
        .join(Camera, Observation.source_camera_id == Camera.cam_id)
        .where(VehicleObservation.vehicle_id == vehicle_id)
        .order_by(Observation.timestamp_capture.asc())
    )
    result = await db.execute(query)
    rows = result.all()
    
    points = []
    for v_obs, obs, cam in rows:
        cam_info = get_camera(cam.cam_id)
        if cam_info:
            points.append({
                "camera_id": cam.cam_id,
                "camera_name": cam.display_name,
                "location": f"{cam.road}, {cam.intersection}",
                "lat": cam_info["lat"],
                "lng": cam_info["lng"],
                "timestamp": obs.timestamp_capture,
                "confidence": v_obs.confidence
            })
            
    return {"points": points}

@router.get("/persons")
async def search_persons(
    gender: Optional[str] = None,
    clothing_color: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Search for person entities."""
    query = select(Person)
    result = await db.execute(query)
    persons = result.scalars().all()
    return persons

@router.get("/persons/{person_id}")
async def get_person(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(["investigator", "command"]))
):
    """Get person details + recent observations."""
    result = await db.execute(select(Person).where(Person.person_id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
