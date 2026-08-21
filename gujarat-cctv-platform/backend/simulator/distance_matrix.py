import json
import math
import os
from typing import Dict, Tuple
from .camera_registry import get_all_cameras

# Demo sequence specific distances
DEMO_DISTANCES = {
    ("CAM-GJ-AHM-SG-0101", "CAM-GJ-AHM-SG-0113"): 3.2,
    ("CAM-GJ-AHM-SG-0113", "CAM-GJ-AHM-SG-0127"): 2.8,
    ("CAM-GJ-AHM-SG-0127", "CAM-GJ-AHM-SG-0144"): 4.1,
    ("CAM-GJ-AHM-SG-0144", "CAM-GJ-AHM-SP-0171"): 8.7,
}

_matrix: Dict[Tuple[str, str], float] = {}

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def _compute_matrix():
    global _matrix
    if _matrix:
        return
    
    cameras = get_all_cameras()
    
    for c1 in cameras:
        for c2 in cameras:
            id1 = c1["cam_id"]
            id2 = c2["cam_id"]
            if id1 == id2:
                _matrix[(id1, id2)] = 0.0
                continue
                
            # Check demo sequence overrides (both directions)
            if (id1, id2) in DEMO_DISTANCES:
                _matrix[(id1, id2)] = DEMO_DISTANCES[(id1, id2)]
                continue
            if (id2, id1) in DEMO_DISTANCES:
                _matrix[(id1, id2)] = DEMO_DISTANCES[(id2, id1)]
                continue
                
            dist = _haversine(c1["latitude"], c1["longitude"], c2["latitude"], c2["longitude"])
            dist *= 1.3 # tortuosity factor
            _matrix[(id1, id2)] = round(dist, 2)

def get_road_distance(c1: str, c2: str) -> float:
    """Returns the road distance in km between two cameras."""
    _compute_matrix()
    return _matrix.get((c1, c2), -1.0)

def get_speed_limit(c1: str, c2: str) -> float:
    """Returns the assumed speed limit in km/h between two cameras."""
    return 60.0 # Default speed limit for demo

def export_matrix(filepath: str):
    _compute_matrix()
    # Convert tuple keys to string for JSON
    json_matrix = {}
    for (id1, id2), dist in _matrix.items():
        if id1 not in json_matrix:
            json_matrix[id1] = {}
        json_matrix[id1][id2] = dist
        
    with open(filepath, 'w') as f:
        json.dump(json_matrix, f, indent=2)

