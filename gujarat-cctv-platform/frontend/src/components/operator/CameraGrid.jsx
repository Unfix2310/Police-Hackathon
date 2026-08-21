import React from 'react';
export default function CameraGrid() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 h-full overflow-y-auto pb-8">
      {[1,2,3,4,5,6].map(i => (
        <div key={i} className="bg-gray-200 rounded aspect-video flex items-center justify-center relative overflow-hidden group">
          <span className="text-gray-400">Feed {i} Offline</span>
          <div className="absolute top-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded">Cam 00{i} - SG Highway</div>
        </div>
      ))}
    </div>
  );
}
