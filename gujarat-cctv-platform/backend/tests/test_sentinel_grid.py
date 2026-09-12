"""
Sentinel Camera Grid Integration Tests
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from simulator.camera_registry import fetch_sentinel_catalogue
from ai.tracker import ObjectTracker, Detection


async def test_sentinel_url_generation():
    assert "@" in settings.SENTINEL_EMAIL
    assert "%40" in settings.sentinel_encoded_email
    assert settings.SENTINEL_RTSP_IP == "103.250.160.189"

    rtsp_url = settings.get_rtsp_url("cam04")
    assert rtsp_url.startswith("rtsp://") and "/stream/cam04" in rtsp_url
    assert settings.sentinel_encoded_email in rtsp_url

    hls_url = settings.get_hls_url("cam04")
    assert hls_url == "https://cctv.corp8.cloud/cam04/index.m3u8"

    webrtc_url = settings.get_webrtc_url("cam04")
    assert webrtc_url.startswith("http://") and "/stream/cam04/whep" in webrtc_url


async def test_sentinel_catalogue_resolution():
    cams = await fetch_sentinel_catalogue()
    assert len(cams) == 30
    assert cams[0]["cam_id"] == "cam01"
    assert cams[-1]["cam_id"] == "cam30"
    assert "/stream/cam01" in cams[0]["rtsp_url"]
    assert "index.m3u8" in cams[0]["hls_url"]


def test_tracker_scene_discontinuity():
    tracker = ObjectTracker(iou_threshold=0.3, track_buffer_ms=1000.0)
    det1 = [Detection(bbox=[100, 100, 200, 200], confidence=0.9, class_id=0, label="person")]

    tracks_t1 = tracker.update(det1, pts_ms=5000.0)
    assert len(tracks_t1) == 1
    track_id_1 = tracks_t1[0].track_id

    # Simulated feed loop (PTS jumps back to 200.0 ms)
    tracks_looped = tracker.update(det1, pts_ms=200.0)
    assert len(tracks_looped) == 1
    track_id_2 = tracks_looped[0].track_id
    assert track_id_2 != track_id_1, "Tracker must reset tracks across scene discontinuity"


if __name__ == "__main__":
    asyncio.run(test_sentinel_url_generation())
    asyncio.run(test_sentinel_catalogue_resolution())
    test_tracker_scene_discontinuity()
    print("✅ All Sentinel grid integration tests passed!")
