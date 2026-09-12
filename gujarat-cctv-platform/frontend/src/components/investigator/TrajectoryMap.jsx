import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

function FitBounds({ bounds }) {
  const map = useMap();
  React.useEffect(() => {
    if (bounds && bounds.length >= 2) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [bounds, map]);
  return null;
}

function createStepIcon(index, isAnomaly = false) {
  const bg = isAnomaly ? '#ef4444' : '#2563eb';
  return L.divIcon({
    className: 'trajectory-marker',
    html: `<div style="width:24px;height:24px;border-radius:50%;background:${bg};color:white;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);">${index + 1}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
}

export default function TrajectoryMap({ steps = [], anomalies = [] }) {
  const anomalyCameraSet = useMemo(() => {
    const s = new Set();
    anomalies.forEach(a => {
      if (a.between) a.between.forEach(c => s.add(c));
    });
    return s;
  }, [anomalies]);

  const validSteps = steps.filter(s => s.lat && s.lng);

  if (validSteps.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm border border-dashed rounded-lg">
        No trajectory data — select an entity from Search
      </div>
    );
  }

  const positions = validSteps.map(s => [s.lat, s.lng]);
  const center = positions[0];

  // Split polyline segments: red for anomalous, blue for normal
  const segments = [];
  for (let i = 0; i < validSteps.length - 1; i++) {
    const isAnomalous = anomalyCameraSet.has(validSteps[i].camera_id) && anomalyCameraSet.has(validSteps[i+1].camera_id);
    segments.push({
      positions: [positions[i], positions[i+1]],
      color: isAnomalous ? '#ef4444' : '#2563eb',
      dashArray: isAnomalous ? '8 6' : undefined,
    });
  }

  return (
    <MapContainer center={center} zoom={12} className="h-full w-full rounded-lg" zoomControl={false}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap'
      />
      <FitBounds bounds={positions} />

      {segments.map((seg, i) => (
        <Polyline
          key={i}
          positions={seg.positions}
          color={seg.color}
          weight={3}
          dashArray={seg.dashArray}
        />
      ))}

      {validSteps.map((step, idx) => (
        <Marker
          key={idx}
          position={[step.lat, step.lng]}
          icon={createStepIcon(idx, anomalyCameraSet.has(step.camera_id))}
        >
          <Popup>
            <div className="text-xs">
              <div className="font-bold">{step.camera_name || step.camera_id}</div>
              <div>{step.timestamp ? new Date(step.timestamp).toLocaleString() : ''}</div>
              {step.speed_from_previous && (
                <div className={step.speed_from_previous > 120 ? 'text-red-600 font-bold' : 'text-slate-600'}>
                  Speed: {step.speed_from_previous.toFixed(0)} km/h
                </div>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
