import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

class ObservationGenerator:
    def __init__(self):
        self.node_id = "edge-mvp-01"
        self.gateway_id = "gw-mvp-01"
        self.model_id = "mvp-pipeline-v1"
        
    def generate(self, 
                camera_id: str, 
                timestamp: datetime,
                obs_type: str,
                track_id: int,
                bbox: List[int],
                confidence: float,
                attributes: Dict[str, Any],
                frame_ref: str = "",
                video_ref: str = "") -> Dict[str, Any]:
                
        obs_id = str(uuid.uuid4())
        
        process_time = datetime.now(timezone.utc)
        latency_ms = int((process_time - timestamp).total_seconds() * 1000)
        
        payload = {}
        if obs_type == "VEHICLE":
            payload = {
                "plate": attributes.get("plate"),
                "plate_confidence": attributes.get("plate_confidence"),
                "color": attributes.get("color"),
                "vehicle_class": attributes.get("vehicle_class", "UNKNOWN"),
                "make_model": attributes.get("make_model")
            }
        elif obs_type == "PERSON":
            payload = {
                "clothing": attributes.get("clothing", "Unknown"),
                "bag": attributes.get("bag"),
                "helmet": attributes.get("helmet", False),
                "gender_estimate": attributes.get("gender_estimate")
            }
            
        obs = {
            "observation_id": obs_id,
            "observation_type": obs_type,
            "source_camera_id": camera_id,
            "source_gateway_id": self.gateway_id,
            "source_edge_id": self.node_id,
            "timestamp_capture": timestamp.isoformat(),
            "timestamp_process": process_time.isoformat(),
            "location_lat": 23.0225,
            "location_lng": 72.5714,
            "bounding_box": bbox,
            "track_id": f"T-{track_id}",
            "confidence": float(confidence),
            "payload": payload,
            "feature_vector_ref": None,
            "frame_ref": frame_ref,
            "video_ref": video_ref,
            "frame_offset_ms": 0,
            "crop_ref": None,
            "model_id": self.model_id,
            "model_version": "1.0.0",
            "model_hash": "sha256:mvp",
            "processing_node": self.node_id,
            "processing_latency": max(latency_ms, 1)
        }
        
        hash_str = f"{obs_id}{camera_id}{timestamp.isoformat()}"
        obs["observation_hash"] = hashlib.sha256(hash_str.encode()).hexdigest()
        
        return obs
