import React from 'react';
import CameraGrid from '../components/operator/CameraGrid';
import AlertPanel from '../components/operator/AlertPanel';
import Map from '../components/shared/Map';

export default function OperatorConsole() {
  return (
    <div className="flex h-full gap-4 overflow-hidden pb-4">
      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        <div className="bg-white rounded-lg shadow-sm p-4 flex flex-col flex-1 min-h-[400px]">
          <h2 className="text-lg font-semibold mb-3 text-police-blue shrink-0">Live Camera Feeds</h2>
          <div className="flex-1 overflow-hidden">
            <CameraGrid />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4 flex flex-col flex-1 min-h-[300px]">
           <h2 className="text-lg font-semibold mb-3 text-police-blue shrink-0">Jurisdiction Map</h2>
           <div className="flex-1 rounded overflow-hidden relative">
             <Map />
           </div>
        </div>
      </div>
      <div className="w-80 bg-white rounded-lg shadow-sm p-4 flex flex-col shrink-0 overflow-hidden">
        <h2 className="text-lg font-semibold mb-4 text-saffron shrink-0">Real-time Alerts</h2>
        <div className="flex-1 overflow-hidden">
          <AlertPanel />
        </div>
      </div>
    </div>
  );
}
