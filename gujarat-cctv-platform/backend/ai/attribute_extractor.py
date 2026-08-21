import logging
import cv2
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VehicleAttributeExtractor:
    def __init__(self):
        self.colors = [
            "White", "Black", "Red", "Blue", "Silver", "Grey", "Yellow", "Green", "Unknown"
        ]
        self.color_centroids = np.array([
            [255, 255, 255], # White
            [0, 0, 0],       # Black
            [0, 0, 255],     # Red
            [255, 0, 0],     # Blue
            [192, 192, 192], # Silver
            [128, 128, 128], # Grey
            [0, 255, 255],   # Yellow
            [0, 255, 0],     # Green
        ])

    def _get_dominant_color(self, crop: np.ndarray) -> str:
        if crop is None or crop.size == 0:
            return "Unknown"
            
        try:
            small = cv2.resize(crop, (50, 50))
            h, w = small.shape[:2]
            center = small[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
            mean_bgr = np.mean(center, axis=(0, 1))
            
            distances = np.linalg.norm(self.color_centroids - mean_bgr, axis=1)
            closest_idx = np.argmin(distances)
            return self.colors[closest_idx]
            
        except Exception as e:
            logger.error(f"Color extraction error: {e}")
            return "Unknown"

    def extract(self, crop: np.ndarray, class_id: int) -> Dict[str, Any]:
        color = self._get_dominant_color(crop)
        
        vehicle_class = "UNKNOWN"
        if class_id == 2: vehicle_class = "SEDAN"
        elif class_id == 3: vehicle_class = "TWO_WHEELER"
        elif class_id == 5: vehicle_class = "BUS"
        elif class_id == 7: vehicle_class = "TRUCK"
        
        return {
            "color": color,
            "vehicle_class": vehicle_class,
            "make_model": "Unknown" 
        }

class PersonAttributeExtractor:
    def __init__(self):
        pass
        
    def extract(self, crop: np.ndarray) -> Dict[str, Any]:
        return {
            "clothing": "Unknown",
            "bag": None,
            "helmet": False,
            "gender_estimate": None
        }
