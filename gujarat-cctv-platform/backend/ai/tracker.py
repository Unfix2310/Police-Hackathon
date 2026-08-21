import logging
from typing import List
from pydantic import BaseModel
import numpy as np
from .detector import Detection

logger = logging.getLogger(__name__)

class TrackedObject(BaseModel):
    track_id: int
    bbox: List[int]
    class_id: int
    
class ObjectTracker:
    def __init__(self, iou_threshold: float = 0.3, track_buffer: int = 30):
        self.iou_threshold = iou_threshold
        self.track_buffer = track_buffer
        self.tracker = None
        self.tracks = {}
        self.next_id = 1
            
    def _compute_iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        if inter_area == 0:
            return 0
            
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        return inter_area / float(box1_area + box2_area - inter_area)

    def update(self, detections: List[Detection], frame_id: int) -> List[TrackedObject]:
        if not detections:
            return []
            
        tracked_objects = []
        
        # Simple Greedy IoU matching for the MVP fallback
        unmatched_detections = list(detections)
        matched_tracks = set()
        
        for track_id, track_data in list(self.tracks.items()):
            last_bbox = track_data['bbox']
            last_frame = track_data['frame_id']
            
            # Remove old tracks
            if frame_id - last_frame > self.track_buffer:
                del self.tracks[track_id]
                continue
                
            best_iou = self.iou_threshold
            best_det = None
            
            for det in unmatched_detections:
                if det.class_id != track_data['class_id']:
                    continue
                    
                iou = self._compute_iou(last_bbox, det.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_det = det
                    
            if best_det:
                unmatched_detections.remove(best_det)
                self.tracks[track_id] = {
                    'bbox': best_det.bbox,
                    'class_id': best_det.class_id,
                    'frame_id': frame_id
                }
                tracked_objects.append(TrackedObject(
                    track_id=track_id,
                    bbox=best_det.bbox,
                    class_id=best_det.class_id
                ))
                matched_tracks.add(track_id)
                
        # Register new tracks
        for det in unmatched_detections:
            track_id = self.next_id
            self.next_id += 1
            
            self.tracks[track_id] = {
                'bbox': det.bbox,
                'class_id': det.class_id,
                'frame_id': frame_id
            }
            
            tracked_objects.append(TrackedObject(
                track_id=track_id,
                bbox=det.bbox,
                class_id=det.class_id
            ))
            
        return tracked_objects
