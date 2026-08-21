import logging
import re
from typing import Optional, List
from pydantic import BaseModel
import numpy as np

logger = logging.getLogger(__name__)

class PlateResult(BaseModel):
    plate_text: str
    plate_confidence: float
    plate_bbox: Optional[List[int]] = None

class ANPREngine:
    def __init__(self, conf_threshold: float = 0.6):
        self.conf_threshold = conf_threshold
        self.ocr = None
        self.plate_pattern = re.compile(r"^GJ\d{2}[A-Z]{1,2}\d{4}$")
        
    def _load_model(self):
        if self.ocr is None:
            logger.info("Loading PaddleOCR for ANPR...")
            try:
                from paddleocr import PaddleOCR
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            except Exception as e:
                logger.error(f"Failed to load PaddleOCR: {e}")
                self.ocr = "MOCK"

    def _clean_plate_text(self, text: str) -> str:
        """Fix common OCR mistakes for plates"""
        text = text.upper().replace(' ', '').replace('-', '')
        
        if len(text) >= 2:
            prefix = text[:2]
            prefix = prefix.replace('0', 'O').replace('1', 'I')
            text = prefix + text[2:]
            
        return text

    def _validate_plate(self, text: str) -> bool:
        """Validate if the plate matches Indian format."""
        return bool(self.plate_pattern.match(text))

    def detect_plate(self, vehicle_crop: np.ndarray) -> Optional[PlateResult]:
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None
            
        self._load_model()
        
        if self.ocr == "MOCK":
            return None
            
        try:
            result = self.ocr.ocr(vehicle_crop, cls=True)
            if not result or not result[0]:
                return None
                
            best_text = ""
            best_conf = 0.0
            best_bbox = None
            
            for line in result[0]:
                bbox, (text, conf) = line
                if conf > best_conf:
                    best_text = text
                    best_conf = float(conf)
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    best_bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
                    
            if best_conf >= self.conf_threshold:
                cleaned_text = self._clean_plate_text(best_text)
                if self._validate_plate(cleaned_text) or best_conf > 0.85:
                    return PlateResult(
                        plate_text=cleaned_text,
                        plate_confidence=best_conf,
                        plate_bbox=best_bbox
                    )
        except Exception as e:
            logger.error(f"ANPR error: {e}")
            
        return None
