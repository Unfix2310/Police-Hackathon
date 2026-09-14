# AI Pipeline Specification

> **Classification**: Government Critical Infrastructure  
> **Document Version**: 1.0  
> **Target**: Hackathon MVP (Gujarat CCTV Intelligence Platform)

This document specifies the AI pipeline architecture, model specifications, and algorithmic logic for the Hackathon MVP, derived from the master architecture (§13–19). 

---

## 1. Pipeline Architecture Diagram

```mermaid
flowchart TD
    A[Video File / RTSP Stream] --> B[Frame Extraction]
    B --> C[Detection (YOLOv8m)]
    C --> D[Tracking (Kalman ByteTrack)]
    
    D --> E{Detection Type}
    
    E -->|Vehicle| F[ANPR (Multi-pass Tesseract OCR)]
    E -->|Vehicle| G[Vehicle Attribute Extraction (HSV Color + Geometry)]
    E -->|Person| H[Person Soft-Biometrics (HSV Apparel Profiling)]
    E -->|Person| I[Person Spatial Feasibility Analysis]
    
    F --> J[Observation Generator]
    G --> J
    H --> J
    I --> J
    
    J --> K[Canonical Observation]
    K --> L[Entity Resolution Engine]
    L --> M[Watchlist Check]
    M --> N[Event Publish / Redis PubSub / DB]
```

**Text-Based Flow:**
Video file / RTSP stream → Frame extraction → Detection (YOLOv8m) → Tracking (Kalman ByteTrack) → ANPR (Multi-pass Tesseract) + Attribute Extraction (HSV Color & Geometry) → Observation generation → Entity resolution (Corridor Matching + Plate Index) → Watchlist check → Event publish.

---

## 2. Model Specifications (Hackathon)

| Module | Model / Architecture | Configuration / Details |
|--------|----------------------|-------------------------|
| **Detection** | YOLOv8 (yolov8m) | COCO classes: `0` (person), `2` (car), `3` (motorcycle), `5` (bus), `7` (truck). Conf Threshold: `0.5` |
| **Tracking** | ByteTrack (Kalman Filter) | Dual-threshold IoU association + Kalman motion model. High det thresh: `0.5`, Low det thresh: `0.1`, IoU thresh: `0.3`, Track buffer: 30 frames |
| **ANPR** | Multi-Pass Tesseract OCR | Optimized multi-pass OCR: PSM 7 (single line) & PSM 6 (two-line stacked). Preprocessing: Grayscale, CLAHE, Bilateral filtering, Otsu adaptive thresholding. Syntax-based Indian HSRP/Bharat regex normalization & positional character correction. Conf Threshold: `0.6` |
| **Person Soft-Biometrics** | HSV Apparel Color Profiling & Geometric Scale | Upper/lower torso color histogram analysis in HSV space; aspect ratio and scale estimation; cross-camera spatio-temporal corridor gating (max 20.0 km/h) |
| **Vehicle Attributes** | HSV Color Space + Geometric Classification | Masked HSV histogram binning (White, Black, Red, Blue, Silver/Grey, Yellow/Auto, Green, Orange); class mapping from YOLOv8 (Sedan, SUV, Two-Wheeler, Auto-Rickshaw, Bus, Truck) |


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

## 5. Entity Resolution Logic

The platform implements multi-modal entity resolution combining deterministic plate lookups with soft-biometric spatial-temporal corridor matching:

```python
async def resolve_vehicle(observation: Observation, db: AsyncSession) -> Dict[str, Any]:
    # 1. Exact plate match if plate is readable and confidence > 0.70
    if observation.plate_text and observation.plate_confidence > 0.70:
        match = await db.find_vehicle_by_plate(observation.plate_text)
        if match:
            return {"entity_id": match.vehicle_id, "confidence": 0.95, "method": "EXACT_PLATE"}

    # 2. Soft-biometric corridor matching (Color + Class + Spatio-Temporal Feasibility)
    candidates = await db.get_recent_vehicles(window_sec=600)
    for cand, last_obs in candidates:
        # Hard Physical Feasibility Gate
        implied_speed = haversine(cand.cam, obs.cam) / elapsed_hours
        if implied_speed > settings.PHYSICAL_MAX_VEHICLE_SPEED_KMH: # 150 km/h
            continue # Physically impossible travel

        score = (0.40 * class_similarity) + (0.35 * color_similarity) + (0.25 * temporal_proximity)
        if score >= 0.70:
            return {"entity_id": cand.vehicle_id, "confidence": score, "method": "SOFT_BIOMETRIC"}

    return await create_new_vehicle(observation)

async def resolve_person(observation: Observation, db: AsyncSession) -> Dict[str, Any]:
    candidates = await db.get_recent_persons(window_sec=600)
    for cand, last_obs in candidates:
        # Hard Pedestrian Running Gate
        implied_speed = haversine(cand.cam, obs.cam) / elapsed_hours
        if implied_speed > settings.PHYSICAL_MAX_PEDESTRIAN_SPEED_KMH: # 20 km/h
            continue # Physically impossible foot travel

        score = (0.45 * clothing_color_similarity) + (0.30 * temporal_proximity) + (0.25 * spatial_score)
        if score >= 0.60:
            return {"entity_id": cand.person_id, "confidence": score, "method": "SOFT_BIOMETRIC"}

    return await create_new_person(observation)
```

---

## 6. Spatio-Temporal Feasibility Algorithm

Trajectories and cross-camera hops compute implied transit speeds using Haversine great-circle distance between calibrated camera GPS coordinates:

```python
def check_spatio_temporal_feasibility(cam_a: Camera, cam_b: Camera, t_a: datetime, t_b: datetime, entity_type: str = "vehicle") -> FeasibilityResult:
    elapsed_hours = abs(t_b - t_a).total_seconds() / 3600.0
    if elapsed_hours <= 0:
        return FeasibilityResult(is_plausible=False, score=0.0, label="TELEPORTATION")

    dist_km = haversine(cam_a.latitude, cam_a.longitude, cam_b.latitude, cam_b.longitude)
    speed_kmh = dist_km / elapsed_hours

    if entity_type == "vehicle":
        if speed_kmh > settings.PHYSICAL_MAX_VEHICLE_SPEED_KMH: # 150 km/h
            return FeasibilityResult(is_plausible=False, score=0.0, label="PHYSICALLY_IMPOSSIBLE")
        elif speed_kmh > settings.STATUTORY_HIGHWAY_SPEED_LIMIT_KMH: # 120 km/h
            score = max(0.1, settings.STATUTORY_HIGHWAY_SPEED_LIMIT_KMH / speed_kmh)
            return FeasibilityResult(is_plausible=True, score=score, label="SPEED_ANOMALY")
        else:
            return FeasibilityResult(is_plausible=True, score=1.0, label="PLAUSIBLE")
    else:  # person
        if speed_kmh > settings.PHYSICAL_MAX_PEDESTRIAN_SPEED_KMH: # 20 km/h
            return FeasibilityResult(is_plausible=False, score=0.0, label="PHYSICALLY_IMPOSSIBLE")
        elif speed_kmh <= 6.0:  # Walking speed
            score = max(0.2, 1.0 - (speed_kmh / 20.0))
            return FeasibilityResult(is_plausible=True, score=score, label="PLAUSIBLE_WALKING")
        else:  # Running / transit
            score = max(0.1, 0.7 - (speed_kmh / 30.0))
            return FeasibilityResult(is_plausible=True, score=score, label="PLAUSIBLE_RUNNING")
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
