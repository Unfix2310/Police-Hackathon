import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import CameraMarker from './CameraMarker';
import { SENTINEL_FALLBACK_CAMS } from '../operator/sentinel_cams';
import api from '../../services/api';
import { useAlerts } from '../../hooks/useAlerts';
import { Compass, Eye, Shield } from 'lucide-react';

function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && zoom) {
      map.flyTo(center, zoom, { duration: 1.0 });
    }
  }, [center, zoom, map]);
  return null;
}

export default function Map({ cameras: propCameras, onSelectCamera }) {
  const [cameras, setCameras] = useState(propCameras || []);
  const [viewPreset, setViewPreset] = useState({ center: [23.045, 72.565], zoom: 12, name: 'ahmedabad' });
  const { alerts } = useAlerts ? useAlerts() : { alerts: [] };

  useEffect(() => {
    if (propCameras && propCameras.length > 0) {
      setCameras(propCameras);
      return;
    }

    const loadCams = async () => {
      try {
        const res = await api.get('/cameras?limit=50');
        if (res.data?.cameras && res.data.cameras.length > 0) {
          setCameras(res.data.cameras);
        } else {
          setCameras(SENTINEL_FALLBACK_CAMS);
        }
      } catch {
        setCameras(SENTINEL_FALLBACK_CAMS);
      }
    };
    loadCams();
  }, [propCameras]);

  // Set of camera IDs that currently have active alerts
  const alertCamIds = new Set(
    (alerts || []).map((a) => a.camera_id || a.cam_id).filter(Boolean)
  );

  return (
    <div className="relative h-full w-full rounded-md border border-slate-200 overflow-hidden shadow-inner">
      {/* Top Map Action Toolbar */}
      <div className="absolute top-3 right-3 z-[400] flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-slate-700/60 shadow-lg text-xs">
        <span className="flex items-center gap-1 text-emerald-400 font-semibold mr-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          {cameras.length} Cams
        </span>

        <button
          onClick={() => setViewPreset({ center: [23.045, 72.565], zoom: 12, name: 'ahmedabad' })}
          className={`px-2 py-1 rounded font-medium transition-all ${
            viewPreset.name === 'ahmedabad'
              ? 'bg-blue-600 text-white shadow'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
        >
          Ahmedabad
        </button>

        <button
          onClick={() => setViewPreset({ center: [22.4, 71.5], zoom: 7.5, name: 'gujarat' })}
          className={`px-2 py-1 rounded font-medium transition-all ${
            viewPreset.name === 'gujarat'
              ? 'bg-blue-600 text-white shadow'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
        >
          Gujarat State
        </button>
      </div>

      <MapContainer
        center={viewPreset.center}
        zoom={viewPreset.zoom}
        className="h-full w-full"
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors | Gujarat Police CCTV'
        />

        <MapController center={viewPreset.center} zoom={viewPreset.zoom} />

        {cameras.map((cam) => (
          <CameraMarker
            key={cam.cam_id}
            camera={cam}
            isAlert={alertCamIds.has(cam.cam_id)}
            onSelect={onSelectCamera}
          />
        ))}
      </MapContainer>
    </div>
  );
}
