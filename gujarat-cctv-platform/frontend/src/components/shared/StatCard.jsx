import React from 'react';
export default function StatCard({ title, value, trend, type }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-police-blue">
      <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        <span className={`text-sm ${trend.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>{trend}</span>
      </div>
    </div>
  );
}
