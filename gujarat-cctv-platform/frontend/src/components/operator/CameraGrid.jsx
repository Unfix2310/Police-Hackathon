import React, { useState, useEffect } from 'react';
import CameraCard from './CameraCard';
import api from '../../services/api';

const SENTINEL_FALLBACK_CAMS = Array.from({ length: 30 }, (_, i) => {
  const num = i + 1;
  const id = `cam${num < 10 ? '0' + num : num}`;
  return {
    cam_id: id,
    display_name: `Camera ${num < 10 ? '0' + num : num}`,
    location_type: 'Junction / Bridge',
    rtsp_url: `rtsp://smitchova%40gmail.com:REDACTED_SENTINEL_CREDENTIAL@103.250.160.189:8554/stream/${id}`,
    hls_url: `/api/v1/cameras/${id}/stream/index.m3u8`,
    webrtc_url: `http://smitchova%40gmail.com:REDACTED_SENTINEL_CREDENTIAL@103.250.160.189:8889/stream/${id}/whep`,
    web_url: `/api/v1/cameras/${id}/stream/index.m3u8`,
    status: 'ONLINE'
  };
});

export default function CameraGrid() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const res = await api.get('/cameras?limit=30');
        if (res.data?.cameras && res.data.cameras.length > 0) {
          setCameras(res.data.cameras);
        } else {
          setCameras(SENTINEL_FALLBACK_CAMS);
        }
      } catch (err) {
        console.warn('Could not load cameras from API; using Sentinel Grid catalogue fallback:', err);
        setCameras(SENTINEL_FALLBACK_CAMS);
      } finally {
        setLoading(false);
      }
    };

    fetchCameras();
  }, []);

  if (loading) {
    return <div className="h-full flex items-center justify-center text-gray-500">Loading Sentinel Live Feeds...</div>;
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 h-full overflow-y-auto content-start auto-rows-max pr-2">
      {cameras.map((camera) => (
        <CameraCard key={camera.cam_id} camera={camera} />
      ))}
    </div>
  );
}

