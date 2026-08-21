import React from 'react';
export default function AlertPanel() {
  return (
    <div className="flex-1 overflow-y-auto space-y-3 pr-2">
      {[1,2,3].map(i => (
        <div key={i} className="p-3 bg-red-50 border border-red-100 rounded-md">
          <div className="flex justify-between items-start">
            <span className="font-bold text-red-700 text-sm">Suspicious Vehicle</span>
            <span className="text-xs text-gray-500">2m ago</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Match found for black SUV (GJ01AB1234) at SG Highway</p>
        </div>
      ))}
    </div>
  );
}
