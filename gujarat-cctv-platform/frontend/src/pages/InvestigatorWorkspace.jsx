import React from 'react';
import SearchPanel from '../components/investigator/SearchPanel';
import Map from '../components/shared/Map';
import InvestigationGraph from '../components/investigator/InvestigationGraph';

export default function InvestigatorWorkspace() {
  return (
    <div className="flex h-full gap-4">
      <div className="w-1/3 bg-white rounded-lg shadow p-4 flex flex-col">
        <h2 className="font-semibold text-police-blue mb-4">Entity Search</h2>
        <SearchPanel />
      </div>
      <div className="flex-1 flex flex-col gap-4">
        <div className="bg-white rounded-lg shadow p-4 h-1/2">
          <h2 className="font-semibold text-police-blue mb-4">Spatial Map</h2>
          <div className="h-[calc(100%-2rem)]"><Map /></div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 h-1/2">
          <h2 className="font-semibold text-police-blue mb-4">Investigation Graph</h2>
          <div className="h-[calc(100%-2rem)]"><InvestigationGraph /></div>
        </div>
      </div>
    </div>
  );
}
