import logging
import cv2
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_dominant_color(crop: np.ndarray, region: str = "center") -> str:
    if crop is None or crop.size == 0:
        return "Unknown"
        
    try:
        small = cv2.resize(crop, (50, 50))
        h, w = small.shape[:2]
        
        if region == "top":
            roi = small[0:int(h*0.5), 0:w]
        else:
            roi = small[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
            
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mean_h, mean_s, mean_v = np.mean(hsv, axis=(0, 1))
        
        if mean_v < 50:
            return "Black"
        elif mean_s < 40 and mean_v > 200:
            return "White"
        elif mean_s < 50 and 50 <= mean_v <= 200:
            return "Silver/Grey"
        elif mean_h < 10 or mean_h > 170:
            return "Red"
        elif 100 <= mean_h <= 130:
            return "Blue"
        elif 20 <= mean_h <= 80:
            return "Yellow/Green" if mean_h < 50 else "Green"
        else:
            return "Unknown"
            
    except Exception as e:
        logger.error(f"Color extraction error: {e}")
        return "Unknown"

class VehicleAttributeExtractor:
    def __init__(self):
        pass

    def extract(self, crop: np.ndarray, class_id: int) -> Dict[str, Any]:
        color = get_dominant_color(crop, region="center")
        
        vehicle_class = "UNKNOWN"
        h, w = crop.shape[:2] if crop is not None else (1, 1)
        aspect_ratio = w / float(h) if h > 0 else 1.0

        if class_id == 2: 
            vehicle_class = "SEDAN" if aspect_ratio > 1.2 else "SUV/VAN"
        elif class_id == 3: 
            vehicle_class = "TWO_WHEELER"
        elif class_id == 5: 
            vehicle_class = "BUS"
        elif class_id == 7: 
            vehicle_class = "TRUCK"
            
        if class_id in (2, 3) and ("Yellow" in color or "Green" in color):
            vehicle_class = "AUTO_RICKSHAW"
        
        return {
            "color": color.split('/')[0] if '/' in color else color,
            "vehicle_class": vehicle_class,
            "make_model": "Unknown" 
        }

class PersonAttributeExtractor:
    def __init__(self):
        pass
        
    def extract(self, crop: np.ndarray) -> Dict[str, Any]:
        color = get_dominant_color(crop, region="top")
        
        return {
            "clothing_color": color.split('/')[0] if '/' in color else color,
            "bag": None,
            "helmet": False,
            "gender_estimate": None
        }
