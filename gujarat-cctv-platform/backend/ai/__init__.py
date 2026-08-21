"""
AI Pipeline module for Gujarat CCTV Platform.
"""
from .detector import ObjectDetector, Detection
from .tracker import ObjectTracker, TrackedObject
from .anpr import ANPREngine, PlateResult
from .attribute_extractor import VehicleAttributeExtractor, PersonAttributeExtractor
from .feature_extractor import FeatureExtractor
from .observation_generator import ObservationGenerator
from .pipeline import VideoPipeline

__all__ = [
    "ObjectDetector", "Detection",
    "ObjectTracker", "TrackedObject",
    "ANPREngine", "PlateResult",
    "VehicleAttributeExtractor", "PersonAttributeExtractor",
    "FeatureExtractor",
    "ObservationGenerator",
    "VideoPipeline"
]
