import React, { useState, useEffect } from 'react';
import { SENTINEL_FALLBACK_CAMS } from '../operator/sentinel_cams';

export default function DistrictHealthTable() {
  const [districtData, setDistrictData] = useState([]);

  useEffect(() => {
    // Group 30 cameras by real district
    const counts = {};
    SENTINEL_FALLBACK_CAMS.forEach((c) => {
      const dist = c.district || 'Ahmedabad';
      counts[dist] = (counts[dist] || 0) + 1;
    });

    const rows = Object.entries(counts).map(([dist, camCount]) => ({
      district: dist,
      cameras: camCount,
      status: 'ONLINE',
      alerts: 0,
    }));

    setDistrictData(rows);
  }, []);

  return (
    <div className="h-full overflow-y-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">District</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">Live Feeds</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">Health</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">Active Alerts</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200 text-xs">
          {districtData.map((d) => (
            <tr key={d.district} className="hover:bg-slate-50">
              <td className="px-4 py-2.5 whitespace-nowrap font-medium text-gray-900">{d.district}</td>
              <td className="px-4 py-2.5 whitespace-nowrap text-gray-600">{d.cameras} Connected</td>
              <td className="px-4 py-2.5 whitespace-nowrap font-medium text-emerald-600">
                <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  100%
                </span>
              </td>
              <td className="px-4 py-2.5 whitespace-nowrap text-gray-400 font-mono">0</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
