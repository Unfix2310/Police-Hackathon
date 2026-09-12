"""
ANPR Test Lab API Router (Isolated Mode)

Provides temporary endpoints to benchmark and visually test the baseline ANPR engine
on user-uploaded CCTV video clips (.mp4) and images.
Zero database mutations, zero live RTSP stream interference, zero alerts.
"""

import base64
import os
import shutil
import tempfile
import uuid
import logging
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from ai.detector import ObjectDetector
from ai.anpr import ANPREngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anpr", tags=["ANPR Test Lab"])

# Lazy singletons for test lab to avoid re-allocating models on each request
_detector: Optional[ObjectDetector] = None
_anpr_engine: Optional[ANPREngine] = None

CLASS_NAMES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

def _get_detector() -> ObjectDetector:
    global _detector
    if _detector is None:
        _detector = ObjectDetector(conf_threshold=0.40)
    return _detector

def _get_anpr() -> ANPREngine:
    global _anpr_engine
    if _anpr_engine is None:
        _anpr_engine = ANPREngine(conf_threshold=0.40)
    return _anpr_engine

def _to_base64_jpeg(img: np.ndarray, quality: int = 85) -> str:
    """Encode OpenCV image to base64 JPEG data URL."""
    if img is None or img.size == 0:
        return ""
    success, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        return ""
    encoded = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"

@router.get("/status")
async def anpr_status():
    """Reports status of the baseline ANPR engine."""
    engine = _get_anpr()
    return {
        "status": "ready" if engine.available else "degraded",
        "engine": "Tesseract Baseline",
        "tesseract_cmd": engine.tesseract_cmd,
        "available": engine.available,
        "isolated_mode": True,
        "note": "Baseline testing engine for benchmarking real-world footage."
    }

@router.post("/test-image")
async def test_single_image(file: UploadFile = File(...)):
    """
    Test ANPR on a single uploaded still frame (.jpg / .png).
    Returns vehicles, detected plates, bboxes, and base64 crops.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    detector = _get_detector()
    anpr = _get_anpr()

    detections = detector.detect(frame)
    veh_detections = [d for d in detections if d.class_id in CLASS_NAMES]

    results = []
    h, w = frame.shape[:2]

    for d in veh_detections:
        vx1, vy1, vx2, vy2 = d.bbox
        vx1, vy1 = max(0, vx1), max(0, vy1)
        vx2, vy2 = min(w, vx2), min(h, vy2)
        veh_crop = frame[vy1:vy2, vx1:vx2]
        if veh_crop.size == 0:
            continue

        plate_res = anpr.detect_plate(veh_crop)
        plate_crop_b64 = _to_base64_jpeg(plate_res.plate_crop) if plate_res.plate_crop is not None else ""

        # Map plate bbox back to full frame coordinates
        fb = plate_res.plate_bbox
        full_plate_bbox = [vx1 + fb[0], vy1 + fb[1], vx1 + fb[2], vy1 + fb[3]] if plate_res.status != "NO_PLATE" else None

        results.append({
            "vehicle_class": CLASS_NAMES.get(d.class_id, "Vehicle"),
            "vehicle_confidence": round(d.confidence, 2),
            "vehicle_bbox": [vx1, vy1, vx2, vy2],
            "plate_text": plate_res.plate_text,
            "plate_confidence": plate_res.plate_confidence,
            "plate_bbox": full_plate_bbox,
            "status": plate_res.status,
            "raw_text": plate_res.raw_text,
            "plate_crop_base64": plate_crop_b64,
        })

    return {
        "filename": file.filename,
        "width": w,
        "height": h,
        "total_vehicles": len(results),
        "detections": results,
    }

@router.post("/test-video")
async def test_video(
    file: UploadFile = File(...),
    max_frames: int = Form(60),       # default 60 frames (30s at 2 FPS)
    target_fps: float = Form(2.0),     # strictly 2 FPS per instructions
):
    """
    Process an uploaded CCTV .mp4 video clip at exactly 2 FPS.
    Returns frame-by-frame vehicle & license plate detections with cropped thumbnails.
    Completely isolated from database and live cameras.
    """
    if not file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video (.mp4, .mov, etc.)")

    # Save to a temporary file for OpenCV reading
    temp_dir = tempfile.gettempdir()
    temp_filename = f"cctv_test_{uuid.uuid4().hex}_{file.filename}"
    temp_path = os.path.join(temp_dir, temp_filename)

    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not decode video stream.")

        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_sec = total_video_frames / orig_fps if orig_fps > 0 else 0.0

        # Calculate frame step to sample at target_fps (2.0 FPS)
        step = max(1, int(round(orig_fps / target_fps)))

        detector = _get_detector()
        anpr = _get_anpr()

        frames_data = []
        total_vehicles = 0
        readable_count = 0
        unreadable_count = 0
        no_plate_count = 0

        # Calculate frame indices sampled at target_fps (2.0 FPS)
        sample_indices = []
        cur_idx = 0
        while cur_idx < total_video_frames and len(sample_indices) < max_frames:
            sample_indices.append(cur_idx)
            cur_idx += step

        for processed_count, frame_idx in enumerate(sample_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            pts_sec = frame_idx / orig_fps
            h, w = frame.shape[:2]

            detections = detector.detect(frame)
            veh_detections = [d for d in detections if d.class_id in CLASS_NAMES]

            # Prioritize largest vehicles in frame (closest to camera, max 6 per frame)
            veh_detections.sort(key=lambda d: (d.bbox[2]-d.bbox[0]) * (d.bbox[3]-d.bbox[1]), reverse=True)
            candidate_vehicles = veh_detections[:6]

            frame_veh_results = []
            for d in candidate_vehicles:
                total_vehicles += 1
                vx1, vy1, vx2, vy2 = d.bbox
                vx1, vy1 = max(0, vx1), max(0, vy1)
                vx2, vy2 = min(w, vx2), min(h, vy2)
                veh_crop = frame[vy1:vy2, vx1:vx2]
                if veh_crop.size == 0:
                    continue

                plate_res = anpr.detect_plate(veh_crop)
                plate_b64 = _to_base64_jpeg(plate_res.plate_crop) if plate_res.plate_crop is not None else ""

                fb = plate_res.plate_bbox
                full_plate_bbox = [vx1 + fb[0], vy1 + fb[1], vx1 + fb[2], vy1 + fb[3]] if plate_res.status != "NO_PLATE" else None

                if plate_res.status == "READABLE":
                    readable_count += 1
                elif plate_res.status == "UNREADABLE":
                    unreadable_count += 1
                else:
                    no_plate_count += 1

                frame_veh_results.append({
                    "vehicle_class": CLASS_NAMES.get(d.class_id, "Vehicle"),
                    "vehicle_confidence": round(d.confidence, 2),
                    "vehicle_bbox": [vx1, vy1, vx2, vy2],
                    "plate_text": plate_res.plate_text,
                    "plate_confidence": plate_res.plate_confidence,
                    "plate_bbox": full_plate_bbox,
                    "status": plate_res.status,
                    "raw_text": plate_res.raw_text,
                    "plate_crop_base64": plate_b64,
                })

            # Also generate a lightweight frame thumbnail for quick inspection
            thumb_h, thumb_w = int(h * (480 / max(1, w))), 480
            thumb = cv2.resize(frame, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)
            frame_thumb_b64 = _to_base64_jpeg(thumb, quality=70)

            frames_data.append({
                "frame_index": frame_idx,
                "processed_index": processed_count,
                "timestamp_sec": round(pts_sec, 2),
                "timestamp_formatted": _format_time(pts_sec),
                "thumbnail_base64": frame_thumb_b64,
                "detections": frame_veh_results,
            })

        cap.release()

        return {
            "status": "success",
            "metadata": {
                "filename": file.filename,
                "duration_sec": round(duration_sec, 2),
                "original_fps": round(orig_fps, 2),
                "processed_fps": target_fps,
                "width": video_width,
                "height": video_height,
                "frames_analyzed": len(frames_data),
                "total_vehicles_detected": total_vehicles,
                "readable_plates": readable_count,
                "unreadable_plates": unreadable_count,
                "no_plate_vehicles": no_plate_count,
            },
            "frames": frames_data,
        }

    except Exception as e:
        logger.error(f"Error processing test video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing video: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
