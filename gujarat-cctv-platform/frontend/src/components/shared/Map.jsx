import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import CameraMarker from './CameraMarker';
import { SENTINEL_FALLBACK_CAMS } from '../operator/sentinel_cams';
import api from '../../services/api';
import { useAlerts } from '../../hooks/useAlerts';
import { Loader2, ChevronDown } from 'lucide-react';

function MapController({ viewTarget }) {
  const map = useMap();
  useEffect(() => {
    if (!viewTarget) return;
    if (viewTarget.bounds) {
      map.fitBounds(viewTarget.bounds, { padding: [40, 40], maxZoom: 13, animate: true, duration: 1.0 });
    } else if (viewTarget.center && viewTarget.zoom) {
      map.flyTo(viewTarget.center, viewTarget.zoom, { duration: 1.0 });
    }
  }, [viewTarget, map]);
  return null;
}

export default function Map({ cameras: propCameras, onSelectCamera }) {
  const [cameras, setCameras] = useState(
    propCameras && propCameras.length > 0 ? propCameras : SENTINEL_FALLBACK_CAMS
  );
  const [loading, setLoading] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState('ALL');
  const [viewTarget, setViewTarget] = useState({ center: [23.045, 72.565], zoom: 12 });
  const { alerts } = useAlerts ? useAlerts() : { alerts: [] };

  useEffect(() => {
    if (propCameras && propCameras.length > 0) {
      setCameras(propCameras);
      return;
    }

    const loadCams = async () => {
      try {
        const res = await api.get('/cameras?limit=100');
        if (res.data?.cameras && res.data.cameras.length > 0) {
          setCameras(res.data.cameras);
        }
      } catch (err) {
        console.warn('Map: Could not load cameras from API; using Sentinel catalogue fallback:', err);
      }
    };
    loadCams();
  }, [propCameras]);

  // Dynamically compute unique districts and camera count per district from live camera data
  const districtCounts = useMemo(() => {
    const mapCounts = {};
    cameras.forEach((cam) => {
      const dist = cam.district || 'Ahmedabad';
      mapCounts[dist] = (mapCounts[dist] || 0) + 1;
    });
    return Object.entries(mapCounts).sort(([a], [b]) => a.localeCompare(b));
  }, [cameras]);

  // Filtered cameras based on dropdown selection
  const displayedCameras = useMemo(() => {
    if (selectedDistrict === 'ALL') return cameras;
    return cameras.filter(
      (c) => (c.district || '').toLowerCase() === selectedDistrict.toLowerCase()
    );
  }, [cameras, selectedDistrict]);

  const handleDistrictChange = (district) => {
    setSelectedDistrict(district);
    if (district === 'ALL') {
      setViewTarget({ center: [22.4, 71.5], zoom: 7.5 });
      return;
    }

    const distCams = cameras.filter(
      (c) => (c.district || '').toLowerCase() === district.toLowerCase()
    );

    if (distCams.length === 0) return;

    const lats = distCams.map((c) => c.lat || c.latitude).filter(Boolean);
    const lngs = distCams.map((c) => c.lng || c.longitude).filter(Boolean);

    if (lats.length === 0 || lngs.length === 0) return;

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    if (minLat === maxLat && minLng === maxLng) {
      setViewTarget({ center: [minLat, minLng], zoom: 13 });
    } else {
      setViewTarget({ bounds: [[minLat, minLng], [maxLat, maxLng]] });
    }
  };

  // Set of camera IDs that currently have active alerts
  const alertCamIds = new Set(
    (alerts || []).map((a) => a.camera_id || a.cam_id).filter(Boolean)
  );

  return (
    <div className="relative h-full w-full rounded-md border border-slate-200 overflow-hidden shadow-inner">
      {/* Top Map Action Toolbar */}
      <div className="absolute top-3 right-3 z-[400] flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/60 shadow-lg text-xs">
        {/* Dynamic Cam Counter with Loading indicator */}
        <span className="flex items-center gap-1.5 text-emerald-400 font-semibold mr-1">
          {loading ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
              <span className="text-slate-300">Loading Feeds...</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>
                {displayedCameras.length} {displayedCameras.length === 1 ? 'Cam' : 'Cams'}
                {selectedDistrict !== 'ALL' && ` in ${selectedDistrict}`}
              </span>
            </>
          )}
        </span>

        {/* Dynamic District Dropdown */}
        <div className="relative flex items-center">
          <select
            value={selectedDistrict}
            onChange={(e) => handleDistrictChange(e.target.value)}
            disabled={loading}
            aria-label="Select Gujarat District"
            className="bg-slate-800 hover:bg-slate-750 text-white font-medium pl-2.5 pr-7 py-1 rounded border border-slate-600 text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer appearance-none disabled:opacity-50"
          >
            <option value="ALL">
              All Gujarat ({cameras.length})
            </option>
            {districtCounts.map(([dist, count]) => (
              <option key={dist} value={dist}>
                {dist} ({count})
              </option>
            ))}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 pointer-events-none" />
        </div>
      </div>

      <MapContainer
        center={viewTarget.center || [23.045, 72.565]}
        zoom={viewTarget.zoom || 12}
        className="h-full w-full"
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors | Gujarat Police CCTV'
        />

        <MapController viewTarget={viewTarget} />

        {displayedCameras.map((cam) => (
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
