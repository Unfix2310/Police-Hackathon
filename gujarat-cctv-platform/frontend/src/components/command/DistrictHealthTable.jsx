import React from 'react';
export default function DistrictHealthTable() {
  return (
    <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">District</th>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uptime</th>
          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Alerts</th>
        </tr>
      </thead>
      <tbody className="bg-white divide-y divide-gray-200">
        <tr>
          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Ahmedabad</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">99.9%</td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">24</td>
        </tr>
      </tbody>
    </table>
  );
}
