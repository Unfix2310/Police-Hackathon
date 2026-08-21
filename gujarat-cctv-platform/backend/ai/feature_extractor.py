import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class FeatureExtractor:
    def __init__(self, dim: int = 512):
        self.dim = dim
        
    def extract(self, crop: np.ndarray) -> np.ndarray:
        if crop is None or crop.size == 0:
            return np.zeros(self.dim, dtype=np.float32)
            
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (16, 32))
            vector = resized.flatten().astype(np.float32)
            
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            return vector
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return np.zeros(self.dim, dtype=np.float32)
