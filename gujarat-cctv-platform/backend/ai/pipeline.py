import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
import numpy as np
import cv2

from .detector import ObjectDetector, Detection
from .tracker import ObjectTracker, TrackedObject
from .anpr import ANPREngine
from .attribute_extractor import VehicleAttributeExtractor, PersonAttributeExtractor
from .feature_extractor import FeatureExtractor
from .observation_generator import ObservationGenerator

logger = logging.getLogger(__name__)

class VideoPipeline:
    def __init__(self):
        self.detector = ObjectDetector(conf_threshold=0.5)
        self.tracker = ObjectTracker(iou_threshold=0.3, track_buffer=30)
        self.anpr = ANPREngine(conf_threshold=0.6)
        
        self.veh_attr = VehicleAttributeExtractor()
        self.per_attr = PersonAttributeExtractor()
        self.features = FeatureExtractor(dim=512)
        
        self.obs_gen = ObservationGenerator()
        
    def _crop(self, frame: np.ndarray, bbox: List[int]) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return frame[y1:y2, x1:x2]

    def process_frame(self, frame: np.ndarray, camera_id: str, timestamp: datetime, frame_id: int) -> List[Dict[str, Any]]:
        observations = []
        
        if frame is None or frame.size == 0:
            return observations
            
        try:
            detections = self.detector.detect(frame)
            tracked_objects = self.tracker.update(detections, frame_id)
            
            det_map = {}
            for d in detections:
                det_map[tuple(d.bbox)] = d.confidence
                
            for obj in tracked_objects:
                crop = self._crop(frame, obj.bbox)
                if crop.size == 0:
                    continue
                    
                conf = det_map.get(tuple(obj.bbox), 0.75)
                
                obs_type = "VEHICLE" if obj.class_id in [2, 3, 5, 7] else "PERSON"
                attributes = {}
                
                if obs_type == "VEHICLE":
                    attributes = self.veh_attr.extract(crop, obj.class_id)
                    plate_res = self.anpr.detect_plate(crop)
                    if plate_res:
                        attributes["plate"] = plate_res.plate_text
                        attributes["plate_confidence"] = plate_res.plate_confidence
                        
                elif obs_type == "PERSON":
                    attributes = self.per_attr.extract(crop)
                    
                feat_vec = self.features.extract(crop)
                attributes["features"] = feat_vec.tolist()
                
                obs = self.obs_gen.generate(
                    camera_id=camera_id,
                    timestamp=timestamp,
                    obs_type=obs_type,
                    track_id=obj.track_id,
                    bbox=obj.bbox,
                    confidence=conf,
                    attributes=attributes
                )
                
                observations.append(obs)
                
        except Exception as e:
            logger.error(f"Error processing frame {frame_id}: {e}", exc_info=True)
            
        return observations
        
    def process_video(self, video_path: str, camera_id: str, sample_fps: int = 2) -> List[Dict[str, Any]]:
        all_obs = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return all_obs
            
        orig_fps = cap.get(cv2.CAP_PROP_FPS)
        if orig_fps <= 0: orig_fps = 25
        
        frame_interval = max(1, int(orig_fps / sample_fps))
        frame_id = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_id % frame_interval == 0:
                timestamp = datetime.now(timezone.utc) 
                obs = self.process_frame(frame, camera_id, timestamp, frame_id)
                all_obs.extend(obs)
                
            frame_id += 1
            
        cap.release()
        return all_obs
