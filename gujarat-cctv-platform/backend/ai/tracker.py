import logging
from typing import List, Optional, Tuple, Dict
from pydantic import BaseModel
import numpy as np
from .detector import Detection

logger = logging.getLogger(__name__)


class TrackedObject(BaseModel):
    track_id: int
    bbox: List[int]
    class_id: int


class KalmanBoxTracker:
    """
    Kalman Filter for tracking bounding boxes in image space [x1, y1, x2, y2].
    State vector: [x1, y1, x2, y2, vx1, vy1, vx2, vy2]^T
    Measurement vector: [x1, y1, x2, y2]^T
    """
    def __init__(self, bbox: List[int]):
        self.dim_x = 8
        self.dim_z = 4

        # Initial state: positions initialized, velocities zero
        self.x = np.zeros((8, 1), dtype=np.float32)
        self.x[:4, 0] = [float(b) for b in bbox]

        # State covariance P: moderate initial uncertainty on positions, high on velocity
        self.P = np.eye(8, dtype=np.float32) * 10.0
        self.P[4:, 4:] *= 100.0

        # Measurement matrix H
        self.H = np.zeros((4, 8), dtype=np.float32)
        self.H[:4, :4] = np.eye(4, dtype=np.float32)

        # Measurement noise covariance R
        self.R = np.eye(4, dtype=np.float32) * 1.0

        # Base process noise covariance Q
        self.Q = np.eye(8, dtype=np.float32) * 0.01
        self.Q[4:, 4:] *= 0.1

        self.last_pts_ms = 0.0

    def predict(self, pts_ms: float) -> List[int]:
        """Advance the state vector and return predicted bounding box."""
        dt = max(1.0, pts_ms - self.last_pts_ms) if self.last_pts_ms > 0 else 50.0
        self.last_pts_ms = pts_ms

        # Transition matrix F
        F = np.eye(8, dtype=np.float32)
        for i in range(4):
            F[i, i + 4] = dt / 1000.0  # seconds

        # Predict state and covariance
        self.x = np.dot(F, self.x)
        self.P = np.dot(np.dot(F, self.P), F.T) + self.Q

        return self.get_state()

    def update(self, bbox: List[int]):
        """Update Kalman filter state with new detection measurement."""
        z = np.array(bbox, dtype=np.float32).reshape((4, 1))

        # Innovation / residual: y = z - Hx
        y = z - np.dot(self.H, self.x)

        # Innovation covariance: S = H P H^T + R
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R

        # Kalman gain: K = P H^T S^-1
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        # Update state: x = x + K y
        self.x = self.x + np.dot(K, y)

        # Update covariance: P = (I - KH) P
        I = np.eye(self.dim_x, dtype=np.float32)
        self.P = np.dot(I - np.dot(K, self.H), self.P)

    def get_state(self) -> List[int]:
        """Return current bounding box estimate as integer list [x1, y1, x2, y2]."""
        b = self.x[:4, 0]
        x1 = int(round(b[0]))
        y1 = int(round(b[1]))
        x2 = int(round(b[2]))
        y2 = int(round(b[3]))
        if x2 < x1:
            x2 = x1 + 1
        if y2 < y1:
            y2 = y1 + 1
        return [x1, y1, x2, y2]


class ObjectTracker:
    """
    ByteTrack-inspired multi-object tracker with Kalman Filter motion model.
    Associates high-confidence detections first, then recovers occluded/blurred
    objects using low-confidence detections against remaining active tracks.
    """
    def __init__(
        self,
        iou_threshold: float = 0.3,
        track_buffer_ms: float = 1500.0,
        high_conf_threshold: float = 0.5,
        low_conf_threshold: float = 0.15,
    ):
        self.iou_threshold = iou_threshold
        self.track_buffer_ms = track_buffer_ms
        self.high_conf_threshold = high_conf_threshold
        self.low_conf_threshold = low_conf_threshold

        self.tracks: Dict[int, Dict] = {}
        self.next_id = 1

    @staticmethod
    def _compute_iou(box1: List[int], box2: List[int]) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        inter_w = max(0, x2 - x1)
        inter_h = max(0, y2 - y1)
        inter_area = inter_w * inter_h
        if inter_area == 0:
            return 0.0
        box1_area = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
        box2_area = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])
        denom = float(box1_area + box2_area - inter_area)
        return inter_area / denom if denom > 0 else 0.0

    def _match_detections_to_tracks(
        self,
        candidate_detections: List[Detection],
        track_ids: List[int],
        iou_thresh: float,
    ) -> Tuple[List[Tuple[int, Detection]], List[int], List[Detection]]:
        """Greedy / priority IoU association between track predictions and detections."""
        matches = []
        unmatched_tracks = set(track_ids)
        unmatched_dets = list(candidate_detections)

        # Build IoU matrix
        iou_pairs = []
        for t_id in track_ids:
            t_data = self.tracks[t_id]
            t_box = t_data["predicted_box"]
            for det in unmatched_dets:
                if det.class_id != t_data["class_id"]:
                    continue
                iou = self._compute_iou(t_box, det.bbox)
                if iou >= iou_thresh:
                    iou_pairs.append((iou, t_id, det))

        # Match highest IoU pairs first
        iou_pairs.sort(key=lambda x: x[0], reverse=True)
        for iou, t_id, det in iou_pairs:
            if t_id in unmatched_tracks and det in unmatched_dets:
                matches.append((t_id, det))
                unmatched_tracks.remove(t_id)
                unmatched_dets.remove(det)

        return matches, list(unmatched_tracks), unmatched_dets

    def update(self, detections: List[Detection], pts_ms: float) -> List[TrackedObject]:
        # Handle scene loop point / timestamp reset
        for track_id, track_data in list(self.tracks.items()):
            if pts_ms < track_data["pts_ms"] - 200.0:
                logger.info("Scene discontinuity detected; clearing track state.")
                self.tracks.clear()
                break

        # Step 0: Expire dead tracks
        for track_id, track_data in list(self.tracks.items()):
            if pts_ms - track_data["pts_ms"] > self.track_buffer_ms:
                del self.tracks[track_id]

        if not detections and not self.tracks:
            return []

        # Predict Kalman states for all surviving tracks
        for track_id, track_data in self.tracks.items():
            kf: KalmanBoxTracker = track_data["kf"]
            track_data["predicted_box"] = kf.predict(pts_ms)

        # Partition detections into ByteTrack high and low confidence sets
        dets_high = [d for d in detections if d.confidence >= self.high_conf_threshold]
        dets_low = [
            d for d in detections
            if self.low_conf_threshold <= d.confidence < self.high_conf_threshold
        ]

        active_track_ids = list(self.tracks.keys())

        # Stage 1: Match active tracks with high-confidence detections
        matches_1, unmatched_tracks_1, unmatched_dets_high = self._match_detections_to_tracks(
            dets_high, active_track_ids, self.iou_threshold
        )

        for track_id, det in matches_1:
            kf = self.tracks[track_id]["kf"]
            kf.update(det.bbox)
            self.tracks[track_id]["bbox"] = det.bbox
            self.tracks[track_id]["pts_ms"] = pts_ms

        # Stage 2: Match remaining unmatched tracks with low-confidence detections (occlusion recovery)
        matches_2, unmatched_tracks_2, _ = self._match_detections_to_tracks(
            dets_low, unmatched_tracks_1, self.iou_threshold
        )

        for track_id, det in matches_2:
            kf = self.tracks[track_id]["kf"]
            kf.update(det.bbox)
            self.tracks[track_id]["bbox"] = det.bbox
            self.tracks[track_id]["pts_ms"] = pts_ms

        # Update coasting (unmatched) tracks to their Kalman-predicted position
        for track_id in unmatched_tracks_2:
            if track_id in self.tracks:
                self.tracks[track_id]["bbox"] = self.tracks[track_id]["predicted_box"]

        # Stage 3: Initialize new tracks from unmatched high-confidence detections
        for det in unmatched_dets_high:
            track_id = self.next_id
            self.next_id += 1
            kf = KalmanBoxTracker(det.bbox)
            kf.last_pts_ms = pts_ms
            self.tracks[track_id] = {
                "kf": kf,
                "bbox": det.bbox,
                "predicted_box": det.bbox,
                "class_id": det.class_id,
                "pts_ms": pts_ms,
            }

        # Format tracked objects for caller
        tracked_objects = []
        for track_id, track_data in self.tracks.items():
            # Include tracks that were updated recently (within track buffer window)
            if pts_ms - track_data["pts_ms"] <= self.track_buffer_ms:
                tracked_objects.append(
                    TrackedObject(
                        track_id=track_id,
                        bbox=track_data["bbox"],
                        class_id=track_data["class_id"],
                    )
                )

        return tracked_objects
