from pydantic import BaseModel
from typing import List, Dict, Any

class OverviewStats(BaseModel):
    active_cameras: int
    total_incidents_today: int
    vehicles_tracked_today: int
    persons_identified_today: int

class CameraHealthStats(BaseModel):
    online: int
    offline: int
    degraded: int
    maintenance: int

class TrendData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]
