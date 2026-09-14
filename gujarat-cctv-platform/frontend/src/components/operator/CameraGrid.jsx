import React, { useState, useEffect } from 'react';
import CameraCard from './CameraCard';
import api from '../../services/api';
import { SENTINEL_FALLBACK_CAMS } from './sentinel_cams';

const BATCH_SIZE = 4;
const BATCH_DELAY_MS = 600;

export default function CameraGrid() {
  const [cameras, setCameras] = useState(SENTINEL_FALLBACK_CAMS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const res = await api.get('/cameras?limit=30');
        if (res.data?.cameras && res.data.cameras.length > 0) {
          setCameras(res.data.cameras);
        }
      } catch (err) {
        console.warn('Could not load cameras from API; using Sentinel Grid catalogue fallback:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCameras();
  }, []);

  if (loading && cameras.length === 0) {
    return <div className="h-full flex items-center justify-center text-gray-500">Loading Sentinel Live Feeds...</div>;
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 h-full overflow-y-auto content-start auto-rows-max pr-2">
      {cameras.map((camera, idx) => (
        <CameraCard
          key={camera.cam_id}
          camera={camera}
          loadDelay={Math.floor(idx / BATCH_SIZE) * BATCH_DELAY_MS}
        />
      ))}
    </div>
  );
}

