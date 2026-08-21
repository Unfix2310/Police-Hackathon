import React from 'react';
import CameraGrid from '../components/operator/CameraGrid';
import AlertPanel from '../components/operator/AlertPanel';
import Map from '../components/shared/Map';

export default function OperatorConsole() {
  return (
    <div className="flex h-full gap-4">
      <div className="flex-1 flex flex-col gap-4">
        <div className="bg-white rounded-lg shadow-sm p-4 h-1/2">
          <h2 className="text-lg font-semibold mb-4 text-police-blue">Live Camera Feeds</h2>
          <CameraGrid />
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4 h-1/2">
           <h2 className="text-lg font-semibold mb-4 text-police-blue">Jurisdiction Map</h2>
           <div className="h-[calc(100%-2rem)] rounded overflow-hidden">
             <Map />
           </div>
        </div>
      </div>
      <div className="w-80 bg-white rounded-lg shadow-sm p-4 flex flex-col">
        <h2 className="text-lg font-semibold mb-4 text-saffron">Real-time Alerts</h2>
        <AlertPanel />
      </div>
    </div>
  );
}
