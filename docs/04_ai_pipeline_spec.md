# AI Pipeline Specification

> **Classification**: Government Critical Infrastructure  
> **Document Version**: 1.0  
> **Target**: Hackathon MVP (Gujarat CCTV Intelligence Platform)

This document specifies the AI pipeline architecture, model specifications, and algorithmic logic for the Hackathon MVP, derived from the master architecture (§13–19). 

---

## 1. Pipeline Architecture Diagram

```mermaid
flowchart TD
    A[Video File / Stream] --> B[Frame Extraction]
    B --> C[Detection (YOLOv8)]
    C --> D[Tracking (ByteTrack)]
    
    D --> E{Detection Type}
    
    E -->|Vehicle| F[ANPR (PaddleOCR)]
    E -->|Vehicle| G[Vehicle Attribute Extraction]
    E -->|Person| H[Person ReID Feature Extraction]
    E -->|Person| I[Person Attribute Extraction]
    
    F --> J[Observation Generator]
    G --> J
    H --> J
    I --> J
    
    J --> K[Canonical Observation]
    K --> L[Entity Resolution Engine]
    L --> M[Watchlist Check]
    M --> N[Event Publish / Redis PubSub]
```

**Text-Based Flow:**
Video file → Frame extraction → Detection (YOLOv8) → Tracking (ByteTrack) → ANPR (PaddleOCR) + Attribute Extraction → Observation generation → Entity resolution → Watchlist check → Event publish.

---

## 2. Model Specifications (Hackathon)

| Module | Model / Architecture | Configuration / Details |
|--------|----------------------|-------------------------|
| **Detection** | YOLOv8 (yolov8m) | COCO classes: `0` (person), `2` (car), `3` (motorcycle), `5` (bus), `7` (truck). Conf Threshold: `0.5` |
| **Tracking** | ByteTrack | IoU Threshold: `0.3`, Track buffer: 30 frames |
| **ANPR** | PaddleOCR | Optimized for English alphanumeric, configured for Indian plate formats (GJ XX YY ZZZZ) |
| **Person ReID** | OSNet / ResNet50-BoT | Output vector dimensions: `2048`. Similarity metric: Cosine |
| **Vehicle Attributes** | ResNet18 (Multi-task) | Color (white, black, red, blue, silver, etc.), Type (sedan, SUV, 2-wheeler, truck, auto) |

---

## 3. Input/Output Contracts

### 3.1 Frame Extractor
* **Input**: `video_path` (str), `camera_id` (str)
* **Output**: `frame` (np.ndarray), `timestamp` (float), `camera_id` (str)

### 3.2 Detector
* **Input**: `frame` (np.ndarray)
* **Output**: `List[Detection]`
  ```python
  class Detection(BaseModel):
      bbox: List[int] # [x1, y1, x2, y2]
      class_id: int
      confidence: float
  ```

### 3.3 Tracker
* **Input**: `frame` (np.ndarray), `detections` (List[Detection])
* **Output**: `List[TrackedObject]`
  ```python
  class TrackedObject(BaseModel):
      track_id: int
      bbox: List[int]
      class_id: int
  ```

### 3.4 ANPR
* **Input**: `vehicle_crop` (np.ndarray)
* **Output**: `plate_text` (str), `plate_confidence` (float), `plate_bbox` (List[int])

### 3.5 Attribute Extractor
* **Input**: `crop` (np.ndarray - person/vehicle)
* **Output**: `attributes` (Dict[str, Any]) e.g., `{"color": "red", "type": "sedan"}` or `{"features": [0.1, 0.4, ...]}`

### 3.6 Observation Generator
* **Input**: `tracked_detection` + `attributes` + `camera_id` + `timestamp`
* **Output**: `CanonicalObservation` (JSON Object)

### 3.7 Entity Resolver
* **Input**: `Observation`
* **Output**: `entity_id` (str), `association_confidence` (float)

---

## 4. Configuration 

```python
from pydantic import BaseModel

class PipelineConfig(BaseModel):
    detection_conf_thresh: float = 0.5
    anpr_conf_thresh: float = 0.6
    tracking_iou_thresh: float = 0.3
    reid_similarity_thresh: float = 0.75
    frame_sampling_fps: int = 2
    batch_size: int = 1 # 1 for real-time edge processing
    
    # Optional performance tuning for batch processing
    offline_batch_size: int = 8 
```

---

## 5. Entity Resolution Logic (Pseudocode)

```python
def resolve_entity(observation: Observation) -> EntityMatch:
    if observation.type == "VEHICLE":
        if observation.plate_confidence > 0.8:
            match = db.find_exact_plate(observation.plate_text)
            if match:
                return EntityMatch(entity_id=match.id, confidence=0.95, method="EXACT_PLATE")
        
        # Partial match + attributes fallback
        candidates = db.find_partial_plate(observation.plate_text)
        for cand in candidates:
            if cand.color == observation.attributes['color'] and cand.type == observation.attributes['type']:
                return EntityMatch(entity_id=cand.id, confidence=0.75, method="PARTIAL_ATTR")
                
        return create_new_vehicle_entity(observation)

    elif observation.type == "PERSON":
        candidates = vector_db.search_knn(observation.features, top_k=5)
        for cand in candidates:
            if cand.similarity > CONFIG.reid_similarity_thresh:
                # Validate with spatio-temporal feasibility
                feasibility = check_spatio_temporal_feasibility(observation, cand.last_observation)
                if feasibility.is_plausible:
                    final_score = (cand.similarity * 0.7) + (feasibility.score * 0.3)
                    return EntityMatch(entity_id=cand.id, confidence=final_score, method="REID_ST")
                    
        return create_new_person_entity(observation)
```

---

## 6. Spatio-Temporal Feasibility Algorithm

Based on §19 of the architecture:

```python
def check_spatio_temporal_feasibility(obs_a: Observation, obs_b: Observation) -> FeasibilityResult:
    # 1. Calculate Time Difference (in hours)
    time_diff_hr = abs(obs_b.timestamp - obs_a.timestamp) / 3600.0
    
    if time_diff_hr == 0:
        return FeasibilityResult(is_plausible=False, score=0.0, reason="Simultaneous")

    # 2. Lookup Road Distance (km)
    # Uses pre-computed distance matrix or PostGIS lookup
    distance_km = road_network_distance(obs_a.location, obs_b.location)

    # 3. Calculate Required Speed
    required_speed_kmh = distance_km / time_diff_hr

    # 4. Determine Feasibility Context (Assuming City context for MVP)
    if required_speed_kmh < 40:
        return FeasibilityResult(is_plausible=True, score=1.0, label="PLAUSIBLE")
    elif 40 <= required_speed_kmh <= 60:
        return FeasibilityResult(is_plausible=True, score=0.8, label="POSSIBLE")
    elif 60 < required_speed_kmh <= 80:
        return FeasibilityResult(is_plausible=False, score=0.4, label="LOW_PLAUSIBILITY")
    else:
        return FeasibilityResult(is_plausible=False, score=0.0, label="IMPLAUSIBLE")
```

---

## 7. Watchlist Matching Logic (Pseudocode)

```python
def check_watchlist(entity_match: EntityMatch, observation: Observation):
    if observation.type == "VEHICLE" and observation.plate_text:
        wl_entry = redis.hget("watchlist:vehicles", observation.plate_text)
        if wl_entry:
            publish_alert(
                alert_type="WATCHLIST_MATCH",
                priority="P1",
                entity=entity_match,
                details=f"Stolen Vehicle Match: {observation.plate_text}"
            )
            
    elif observation.type == "PERSON":
        # Search against watchlist vector space
        wl_candidates = vector_db.search_knn(observation.features, namespace="watchlist_persons", top_k=1)
        if wl_candidates and wl_candidates[0].similarity > 0.85:
            publish_alert(
                alert_type="WATCHLIST_MATCH",
                priority="P2",
                entity=entity_match,
                details=f"Wanted Person Appearance Match (Conf: {wl_candidates[0].similarity})"
            )
```

---

## 8. Performance Targets

| Stage | Latency Target (Hackathon) | Latency Target (Production) | Throughput / Hardware |
|-------|----------------------------|-----------------------------|------------------------|
| YOLOv8 Detect | < 100 ms | < 50 ms | 1 stream per T4 GPU |
| Tracker | < 10 ms | < 10 ms | CPU bound |
| ANPR / OCR | < 150 ms | < 50 ms | Edge / GPU |
| ReID / Attr | < 50 ms | < 20 ms | Edge / GPU |
| Overall Pipeline | **< 350 ms per frame** | **< 100 ms per frame** | Real-time at 2 FPS sample rate |

---

## 9. Error Handling

* **Detection Fails**: Frame is dropped from inference pipeline; telemetry logged for model monitoring.
* **ANPR Unreadable**: Vehicle observation is generated WITHOUT plate info, relying entirely on color/type attributes for entity matching.
* **Tracker Loses Object**: A new Track ID is assigned upon re-detection; entity resolver is responsible for merging them if features match.
* **DB/Redis Timeout**: Fail-open; observations are cached locally on the edge (mocked in hackathon via memory buffer) until the connection is restored.

---

## 10. Sample Processing Output

**Input Frame:** `18-32-14.jpg` from `CAM-GJ-AHM-SG-0142`

**1. Detections:**
* `Track 1`: Bbox [100, 200, 300, 400], Class: Car, Conf: 0.94
* `Track 2`: Bbox [400, 150, 450, 300], Class: Person, Conf: 0.88

**2. Observations Generated:**
```json
{
  "observation_id": "obs-1234-5678",
  "source_camera_id": "CAM-GJ-AHM-SG-0142",
  "timestamp_capture": "2026-08-19T18:32:14.237Z",
  "observation_type": "VEHICLE",
  "attributes": {
    "plate_text": "GJ01AB1234",
    "plate_confidence": 0.96,
    "color": "White",
    "type": "Sedan"
  }
}
```

**3. Entity Association:**
* System queries exact plate `GJ01AB1234`.
* Finds existing `Vehicle V-4521`.
* Outputs: `Matched V-4521 with Conf 0.95 (Method: EXACT_PLATE)`.

**4. Event Publish:**
* Observation added to Redis PubSub `observations.vehicle`.
* Spatio-Temporal graph updated for `V-4521` at `CAM-GJ-AHM-SG-0142`.
