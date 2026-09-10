import React from 'react';
import { Route, Clock } from 'lucide-react';

export default function TrajectoryTimeline({ steps = [] }) {
  if (!steps || steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-slate-400 h-full border border-dashed rounded-lg">
        <Route className="w-8 h-8 mb-2 text-slate-300" />
        <span className="text-sm font-medium text-slate-600">No Active Trajectory Selected</span>
        <p className="text-xs text-slate-400 mt-1 max-w-[220px]">
          Execute a search or select an entity to reconstruct its chronological journey across cameras.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
      {steps.map((step, idx) => (
        <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
          <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-blue-600 text-white font-bold text-xs shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
            {idx + 1}
          </div>
          <div className="w-[calc(100%-3.5rem)] md:w-[calc(50%-2rem)] p-3 rounded border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between mb-1">
              <div className="font-semibold text-xs text-slate-900">{step.camera_name || step.camera_id}</div>
              <time className="text-[10px] font-medium text-blue-600 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {step.timestamp ? new Date(step.timestamp).toLocaleTimeString() : ''}
              </time>
            </div>
            <div className="text-xs text-slate-600">{step.location || step.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
