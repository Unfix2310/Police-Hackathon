import React from 'react';
export default function TrajectoryTimeline() {
  return (
    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
      {[1,2,3].map(i => (
        <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
          <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-300 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
            {i}
          </div>
          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between mb-1">
              <div className="font-bold text-slate-900">Camera {i}</div>
              <time className="text-xs font-medium text-amber-500">10:{i}5 AM</time>
            </div>
            <div className="text-sm text-slate-500">Observation details...</div>
          </div>
        </div>
      ))}
    </div>
  );
}
