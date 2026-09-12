"""
RTSP / HLS Stream Worker — v4.1 with Entity Resolution & Co-Observation Wiring

Reads video frames from Sentinel CCTV streams, runs YOLOv8 detection,
and for each detected object:
  1. Generates a canonical observation (with real camera GPS)
  2. Persists to the observations table
  3. Resolves to a persistent Vehicle / Person entity via soft-biometric matching
  4. When a person and vehicle co-appear in the same frame, feeds the pair
     into the v4.1 Interaction Engine for state-machine transitions
"""

import asyncio
import os
import logging
import cv2
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from ai.pipeline import VideoPipeline
from database import async_session_maker
from models.observation import Observation

logger = logging.getLogger(__name__)


class RTSPStreamWorker:
    def __init__(self, camera_id: str, rtsp_url: str, pipeline: VideoPipeline, target_fps: int = 2, fallback_url: Optional[str] = None):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.fallback_url = fallback_url
        self.pipeline = pipeline
        self.target_fps = target_fps
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        # Cache camera metadata for geo-coordinates
        self._cam_lat: float = 23.0225
        self._cam_lng: float = 72.5714
        self._cam_district: str = "Ahmedabad"
        self._cam_station: str = "Unknown"
        self._load_camera_meta()

    def _load_camera_meta(self):
        """Load camera coordinates from the registry."""
        try:
            from simulator.camera_registry import get_camera
            cam = get_camera(self.camera_id)
            if cam:
                self._cam_lat = cam.get("latitude") or cam.get("lat") or 23.0225
                self._cam_lng = cam.get("longitude") or cam.get("lng") or 72.5714
                self._cam_district = cam.get("district", "Ahmedabad")
                self._cam_station = cam.get("police_station", "Unknown")
                logger.info(f"Camera {self.camera_id} geo: ({self._cam_lat}, {self._cam_lng}) district={self._cam_district}")
        except Exception as e:
            logger.warning(f"Could not load camera metadata for {self.camera_id}: {e}")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._process_stream())
        logger.info(f"Started RTSP stream worker for {self.camera_id}")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped RTSP stream worker for {self.camera_id}")

    async def _process_stream(self):
        frame_interval = 1.0 / self.target_fps
        retry_delay = 2.0
        max_retry_delay = 30.0
        rtsp_fail_count = 0

        # Force RTSP over TCP
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        video_source = self.rtsp_url

        while self.is_running:
            # If RTSP repeatedly fails (e.g. port 8554 blocked), switch to HLS fallback
            if rtsp_fail_count >= 3 and self.fallback_url:
                if video_source != self.fallback_url:
                    logger.warning(f"RTSP port 8554 inaccessible for {self.camera_id}; falling back to HLS endpoint: {self.fallback_url}")
                    video_source = self.fallback_url

            logger.info(f"Connecting to video stream for {self.camera_id}: {video_source}")
            cap = await asyncio.to_thread(cv2.VideoCapture, video_source, cv2.CAP_FFMPEG)

            if not cap.isOpened():
                rtsp_fail_count += 1
                logger.error(f"Failed to open stream {video_source}. Retrying in {retry_delay:.1f}s (attempt {rtsp_fail_count})...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, max_retry_delay)
                continue

            logger.info(f"Successfully connected to {video_source}")
            retry_delay = 2.0  # Reset backoff on successful connection
            rtsp_fail_count = 0

            frame_id = 0
            consecutive_misses = 0
            base_stream_time: Optional[datetime] = None
            last_pts_ms = -1.0

            try:
                while self.is_running and cap.isOpened():
                    loop_start = time.time()

                    ret, frame = await asyncio.to_thread(cap.read)
                    if not ret:
                        # Inter-frame gaps do not immediately crash or stall the pipeline
                        consecutive_misses += 1
                        if consecutive_misses < 3:
                            await asyncio.sleep(0.05)
                            continue
                        logger.warning(f"Stream {video_source} reached gap / end-of-stream. Reconnecting with backoff...")
                        break

                    consecutive_misses = 0

                    # Drive all timing strictly from PTS (Presentation Timestamp), never frame arrival time
                    pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

                    # Handle feed loop point / scene discontinuity (PTS resets or drops)
                    if base_stream_time is None or (last_pts_ms >= 0 and pts_ms < last_pts_ms - 100.0):
                        base_stream_time = datetime.now(timezone.utc)

                    frame_timestamp = (
                        base_stream_time + timedelta(milliseconds=pts_ms)
                        if pts_ms > 0
                        else datetime.now(timezone.utc)
                    )
                    last_pts_ms = pts_ms

                    # Run blocking AI pipeline in a thread pool
                    observations_dicts = await asyncio.to_thread(
                        self.pipeline.process_frame, frame, self.camera_id, frame_timestamp, frame_id, pts_ms,
                        self._cam_lat, self._cam_lng
                    )

                    if observations_dicts:
                        await self._persist_and_resolve(observations_dicts, frame_timestamp)

                    frame_id += 1

                    processing_time = time.time() - loop_start
                    sleep_time = frame_interval - processing_time
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    else:
                        await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                logger.info(f"Stream worker for {self.camera_id} cancelled")
                break
            except Exception as e:
                # Decoder warnings on join are logged, not fatal
                logger.warning(f"Warning / transient error processing stream {video_source}: {e}")
            finally:
                cap.release()

            if self.is_running:
                logger.info(f"Reconnecting {self.camera_id} in {retry_delay:.1f}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, max_retry_delay)

    async def _persist_and_resolve(self, observations_dicts: List[Dict[str, Any]], frame_timestamp: datetime):
        """
        Persist observations AND resolve entities in a single DB transaction.
        Also detects person-vehicle co-observations and feeds the interaction engine.
        Checks resolved entities against active watchlists.
        """
        from engine.entity_resolver import get_entity_resolver
        from engine.watchlist import get_watchlist_matcher

        resolver = get_entity_resolver()
        watchlist = get_watchlist_matcher()

        try:
            async with async_session_maker() as db:
                # Lazy-load watchlist entries on first frame
                if not watchlist._loaded:
                    await watchlist.load_watchlist(db)

                person_obs_list = []   # Track person observations for co-observation detection
                vehicle_obs_list = []  # Track vehicle observations for co-observation detection

                for obs_dict in observations_dicts:
                    obs_id = str(uuid.uuid4())
                    ts = datetime.fromisoformat(obs_dict["timestamp_capture"])

                    # ── 1. Insert raw observation ─────────────────────────────
                    db_obs = Observation(
                        observation_id=obs_id,
                        timestamp_capture=ts,
                        observation_type=obs_dict["observation_type"],
                        source_camera_id=obs_dict["source_camera_id"],
                        source_gateway_id=obs_dict["source_gateway_id"],
                        source_edge_id=obs_dict["source_edge_id"],
                        bounding_box=obs_dict["bounding_box"],
                        track_id=obs_dict["track_id"],
                        confidence=obs_dict["confidence"],
                        payload=obs_dict["payload"],
                    )
                    db.add(db_obs)

                    # ── 2. Resolve entity ─────────────────────────────────────
                    payload = obs_dict.get("payload", {})
                    obs_type = obs_dict["observation_type"]
                    conf = obs_dict["confidence"]

                    try:
                        if obs_type == "VEHICLE":
                            result = await resolver.resolve_vehicle(
                                obs_id=obs_id,
                                timestamp=ts,
                                camera_id=self.camera_id,
                                color=payload.get("color"),
                                vehicle_class=payload.get("vehicle_class"),
                                plate=payload.get("plate"),
                                plate_confidence=payload.get("plate_confidence", 0.0) or 0.0,
                                confidence=conf,
                                db=db,
                            )
                            vehicle_obs_list.append({
                                "entity_id": result["entity_id"],
                                "obs_id": obs_id,
                                "bbox": obs_dict["bounding_box"],
                                "timestamp": ts,
                                "confidence": conf,
                            })
                            if result.get("is_new"):
                                logger.debug(f"New vehicle entity: {result['entity_id']} ({payload.get('color')} {payload.get('vehicle_class')})")

                            # ── 2a. Watchlist check for vehicles ──────────
                            await watchlist.check_vehicle(
                                entity_id=result["entity_id"],
                                plate=payload.get("plate"),
                                color=payload.get("color"),
                                vehicle_class=payload.get("vehicle_class"),
                                camera_id=self.camera_id,
                                observation_id=obs_id,
                                timestamp=ts,
                                db=db,
                            )

                        elif obs_type == "PERSON":
                            clothing_color = payload.get("clothing_color") or payload.get("clothing")
                            result = await resolver.resolve_person(
                                obs_id=obs_id,
                                timestamp=ts,
                                camera_id=self.camera_id,
                                clothing_color=clothing_color,
                                confidence=conf,
                                db=db,
                            )
                            person_obs_list.append({
                                "entity_id": result["entity_id"],
                                "obs_id": obs_id,
                                "bbox": obs_dict["bounding_box"],
                                "timestamp": ts,
                                "confidence": conf,
                            })

                            # ── 2b. Watchlist check for persons ───────────
                            await watchlist.check_person(
                                entity_id=result["entity_id"],
                                clothing_color=clothing_color,
                                camera_id=self.camera_id,
                                observation_id=obs_id,
                                timestamp=ts,
                                db=db,
                            )

                    except Exception as e:
                        logger.warning(f"Entity resolution error for {obs_type}: {e}")

                await db.commit()

                entity_count = len(person_obs_list) + len(vehicle_obs_list)
                logger.info(
                    f"Frame: {len(observations_dicts)} obs, {entity_count} entities "
                    f"({len(vehicle_obs_list)}V, {len(person_obs_list)}P) for {self.camera_id}"
                )

                # ── 3. Co-observation → Interaction Engine ────────────────
                if person_obs_list and vehicle_obs_list:
                    await self._process_co_observations(person_obs_list, vehicle_obs_list, frame_timestamp, db)

        except Exception as e:
            logger.error(f"Error persisting observations/entities for {self.camera_id}: {e}", exc_info=True)

    async def _process_co_observations(
        self,
        persons: List[Dict],
        vehicles: List[Dict],
        timestamp: datetime,
        db,
    ):
        """
        When a Person and a Vehicle are detected in the same frame,
        evaluate spatial proximity and feed into the v4.1 Interaction Engine.
        """
        try:
            from engine.interaction import get_interaction_engine, EntityObservation
        except ImportError:
            return  # Interaction engine not available

        engine = get_interaction_engine()

        for p in persons:
            for v in vehicles:
                # Quick proximity check: do bounding boxes overlap or are near each other?
                p_bbox = p["bbox"]
                v_bbox = v["bbox"]

                if not self._bboxes_proximate(p_bbox, v_bbox):
                    continue

                try:
                    person_obs = EntityObservation(
                        entity_id=p["entity_id"],
                        entity_type="PERSON",
                        observation_id=p["obs_id"],
                        camera_id=self.camera_id,
                        timestamp=timestamp,
                        bbox=p_bbox,
                        confidence=p["confidence"],
                    )
                    vehicle_obs = EntityObservation(
                        entity_id=v["entity_id"],
                        entity_type="VEHICLE",
                        observation_id=v["obs_id"],
                        camera_id=self.camera_id,
                        timestamp=timestamp,
                        bbox=v_bbox,
                        confidence=v["confidence"],
                    )

                    events = await engine.process_co_observation(person_obs, vehicle_obs, db)
                    if events:
                        logger.info(f"Interaction: {len(events)} events for {p['entity_id']} ↔ {v['entity_id']}")

                except Exception as e:
                    logger.debug(f"Co-observation processing error: {e}")

    @staticmethod
    def _bboxes_proximate(bbox1: List[int], bbox2: List[int], margin: int = 80) -> bool:
        """Check if two bounding boxes overlap or are within `margin` pixels."""
        if not bbox1 or not bbox2 or len(bbox1) < 4 or len(bbox2) < 4:
            return False

        x1_a, y1_a, x2_a, y2_a = bbox1
        x1_b, y1_b, x2_b, y2_b = bbox2

        # Expand boxes by margin for proximity detection
        x1_a -= margin
        y1_a -= margin
        x2_a += margin
        y2_a += margin

        # Check overlap
        return not (x2_a < x1_b or x2_b < x1_a or y2_a < y1_b or y2_b < y1_a)
