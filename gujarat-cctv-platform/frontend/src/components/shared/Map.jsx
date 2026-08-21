import React from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';

export default function Map() {
  return (
    <MapContainer center={[23.0225, 72.5714]} zoom={12} className="h-full w-full rounded-md border">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
    </MapContainer>
  );
}
