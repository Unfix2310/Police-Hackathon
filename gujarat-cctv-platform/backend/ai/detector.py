import logging
from typing import List, Optional
import numpy as np
import torch
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Detection(BaseModel):
    bbox: List[int] # [x1, y1, x2, y2]
    class_id: int
    confidence: float

class ObjectDetector:
    def __init__(self, model_name: str = "yolov8m.pt", conf_threshold: float = 0.5):
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # COCO mapping for our targets
        self.target_classes = {
            0: 0, # person
            2: 2, # car
            3: 3, # motorcycle
            5: 5, # bus
            7: 7  # truck
        }
        
    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading YOLO model {self.model_name} on {self.device}...")
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_name)
                if self.device == 'cuda':
                    self.model.to(self.device)
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                raise
                
    def detect(self, frame: np.ndarray) -> List[Detection]:
        self._load_model()
        
        if frame is None or frame.size == 0:
            return []
            
        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            device=self.device,
            classes=list(self.target_classes.keys()),
            verbose=False
        )
        
        detections = []
        if not results:
            return detections
            
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for i in range(len(boxes)):
                box = boxes[i]
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                
                # xyxy format
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bbox = [int(x1), int(y1), int(x2), int(y2)]
                
                detections.append(Detection(
                    bbox=bbox,
                    class_id=cls_id,
                    confidence=conf
                ))
                
        return detections
