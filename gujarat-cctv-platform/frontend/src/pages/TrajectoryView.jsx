import React from 'react';
import TrajectoryMap from '../components/investigator/TrajectoryMap';
import TrajectoryTimeline from '../components/investigator/TrajectoryTimeline';

export default function TrajectoryView() {
  return (
    <div className="flex flex-col h-full gap-4">
      <div className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
        <h2 className="text-xl font-bold text-police-blue">Entity Trajectory Analysis</h2>
        <button className="bg-saffron text-white px-4 py-2 rounded">Export Evidence Package</button>
      </div>
      <div className="flex-1 flex gap-4">
        <div className="w-2/3 bg-white p-4 rounded-lg shadow">
           <div className="h-full"><TrajectoryMap /></div>
        </div>
        <div className="w-1/3 bg-white p-4 rounded-lg shadow overflow-y-auto">
           <TrajectoryTimeline />
        </div>
      </div>
    </div>
  );
}
