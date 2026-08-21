import React from 'react';
import StatCard from '../components/shared/StatCard';
import TrendCharts from '../components/command/TrendCharts';
import DistrictHealthTable from '../components/command/DistrictHealthTable';

export default function CommandDashboard() {
  return (
    <div className="flex flex-col gap-6 h-full overflow-y-auto p-2">
      <h2 className="text-2xl font-bold text-police-blue">State Command Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Active Cameras" value="1,245" trend="+5%" />
        <StatCard title="High Priority Alerts" value="12" trend="-2%" type="danger" />
        <StatCard title="Entities Tracked" value="84,392" trend="+12%" />
        <StatCard title="System Health" value="98.9%" trend="+0.1%" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
        <div className="bg-white p-4 rounded-lg shadow"><TrendCharts /></div>
        <div className="bg-white p-4 rounded-lg shadow overflow-hidden"><DistrictHealthTable /></div>
      </div>
    </div>
  );
}
