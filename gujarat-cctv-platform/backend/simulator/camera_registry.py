import json
import os
import logging
from typing import Dict, List, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)

json_path = os.path.join(os.path.dirname(__file__), "live_cameras_30.json")
if os.path.exists(json_path):
    with open(json_path, "r") as f:
        raw_cams = json.load(f)
    CAMERAS = []
    for c in raw_cams:
        loc = c.get("location", "")
        district = "Junagadh" if "junagadh" in loc.lower() else ("Gir Somnath" if "somnath" in loc.lower() else ("Navsari" if "navsari" in loc.lower() else ("Rajkot" if "rajkot" in loc.lower() else "Ahmedabad")))
        stream_path = f"/api/v1/cameras/{c['cam_id']}/stream/index.m3u8"
        CAMERAS.append({
            "cam_id": c["cam_id"],
            "display_name": c["display_name"],
            "location": loc,
            "rtsp_url": c.get("rtsp_url") or settings.get_rtsp_url(c["cam_id"]),
            "hls_url": stream_path,
            "webrtc_url": c.get("webrtc_url") or settings.get_webrtc_url(c["cam_id"]),
            "web_url": stream_path,
            "police_station": loc,
            "district": district,
            "location_type": "Junction" if "rasta" in loc.lower() or "circle" in loc.lower() or "gate" in loc.lower() else "Bridge/Road",
            "jurisdiction_code": f"GJ-{district[:3].upper()}"
        })
else:
    CAMERAS = []


async def fetch_sentinel_catalogue() -> List[Dict]:
    """
    Fetch the live camera catalogue from https://cctv.corp8.cloud/cameras.json.
    Authenticates with Sentinel login session if needed.
    Falls back to local live_cameras_30.json if unreachable.
    """
    catalogue_url = f"{settings.SENTINEL_CDN_HOST}/cameras.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
            # Login to establish authenticated session cookie
            login_url = f"{settings.SENTINEL_CDN_HOST}/auth/login"
            login_resp = await client.post(
                login_url,
                data={
                    "email": settings.SENTINEL_EMAIL,
                    "password": settings.SENTINEL_PASSWORD
                }
            )
            
            # Fetch cameras catalogue
            resp = await client.get(catalogue_url)
            if resp.status_code == 200:
                catalogue = resp.json()
                if isinstance(catalogue, list) and len(catalogue) > 0:
                    logger.info(f"Successfully fetched {len(catalogue)} cameras from Sentinel catalogue.")
                    cams = []
                    for idx, item in enumerate(catalogue, 1):
                        cam_id = item.get("id")
                        name = item.get("name", cam_id)
                        district = "Junagadh" if "junagadh" in name.lower() else ("Gir Somnath" if "somnath" in name.lower() else ("Navsari" if "navsari" in name.lower() else ("Rajkot" if "rajkot" in name.lower() else "Ahmedabad")))
                        stream_path = f"/api/v1/cameras/{cam_id}/stream/index.m3u8"
                        cams.append({
                            "cam_id": cam_id,
                            "display_name": f"Camera {idx:02d} - {name}",
                            "location": name,
                            "rtsp_url": settings.get_rtsp_url(cam_id),
                            "hls_url": stream_path,
                            "webrtc_url": settings.get_webrtc_url(cam_id),
                            "web_url": stream_path,
                            "police_station": name,
                            "district": district,
                            "location_type": "Junction" if "rasta" in name.lower() or "circle" in name.lower() or "gate" in name.lower() else "Bridge/Road",
                            "jurisdiction_code": f"GJ-{district[:3].upper()}"
                        })
                    return cams
    except Exception as e:
        logger.warning(f"Could not fetch live Sentinel catalogue ({e}); falling back to local registry.")

    return CAMERAS


def get_all_cameras() -> List[Dict]:
    """Returns the list of all live cameras."""
    return CAMERAS


def get_camera(cam_id: str) -> Optional[Dict]:
    """Returns a specific camera by ID."""
    for cam in CAMERAS:
        if cam["cam_id"] == cam_id:
            return cam
    return None

