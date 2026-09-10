import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { Video, ExternalLink, ShieldCheck, MapPin } from 'lucide-react';

const createCameraIcon = (camId, isAlert = false) => {
  const label = camId ? camId.toUpperCase().replace('CAM', '') : 'C';
  const borderColor = isAlert ? '#ef4444' : '#10b981';
  const shadowColor = isAlert ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.4)';
  const pulseHtml = isAlert 
    ? `<span style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: rgba(239, 68, 68, 0.4); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; z-index: -1;"></span>`
    : '';

  return L.divIcon({
    className: 'custom-camera-marker',
    html: `
      <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 28px; height: 28px;">
        ${pulseHtml}
        <div style="width: 26px; height: 26px; border-radius: 50%; background: #0f172a; border: 2px solid ${borderColor}; box-shadow: 0 0 10px ${shadowColor}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 10px; font-family: monospace; cursor: pointer; transition: transform 0.15s ease;">
          ${label}
        </div>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
};

export default function CameraMarker({ camera, isAlert = false, onSelect }) {
  const lat = camera.lat || camera.latitude;
  const lng = camera.lng || camera.longitude;

  if (!lat || !lng) return null;

  const icon = createCameraIcon(camera.cam_id, isAlert);

  const handleFocus = () => {
    if (onSelect) {
      onSelect(camera);
    }
    window.dispatchEvent(new CustomEvent('focus-camera', { detail: { camId: camera.cam_id } }));
  };

  return (
    <Marker position={[lat, lng]} icon={icon}>
      <Popup className="custom-police-popup">
        <div className="p-1 min-w-[220px] text-slate-800 font-sans">
          <div className="flex items-center justify-between gap-2 border-b border-slate-200 pb-2 mb-2">
            <div className="flex items-center gap-1.5">
              <span className="bg-slate-900 text-blue-400 font-bold px-1.5 py-0.5 rounded text-[11px]">
                {camera.cam_id?.toUpperCase()}
              </span>
              <span className="font-semibold text-xs text-slate-900 truncate max-w-[130px]">
                {camera.location || camera.display_name}
              </span>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              LIVE
            </span>
          </div>

          <div className="text-[11px] text-slate-600 space-y-1 mb-3">
            <div className="flex items-center gap-1.5">
              <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
              <span>{camera.district ? `${camera.district} District` : 'Gujarat'}</span>
            </div>
            {camera.police_station && (
              <div className="flex items-center gap-1.5 text-slate-500">
                <ShieldCheck className="w-3 h-3 text-blue-500 shrink-0" />
                <span className="truncate">PS: {camera.police_station}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
            <button
              onClick={handleFocus}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-1 px-2 rounded text-[11px] flex items-center justify-center gap-1 transition-colors"
            >
              <Video className="w-3 h-3" />
              Focus Feed
            </button>
            {camera.hls_url && (
              <a
                href={camera.hls_url}
                target="_blank"
                rel="noreferrer"
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 p-1 rounded border border-slate-300"
                title="Open Stream"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        </div>
      </Popup>
    </Marker>
  );
}
