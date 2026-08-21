import React from 'react';
import DataTable from '../components/shared/DataTable';

export default function SearchView() {
  return (
    <div className="bg-white p-6 rounded-lg shadow h-full">
      <h2 className="text-2xl font-bold text-police-blue mb-6">Advanced Semantic Search</h2>
      <div className="grid grid-cols-4 gap-4 mb-8">
        <input type="text" placeholder="Description (e.g. Red car)" className="border p-2 rounded" />
        <input type="text" placeholder="License Plate" className="border p-2 rounded" />
        <input type="datetime-local" className="border p-2 rounded" />
        <button className="bg-police-blue text-white p-2 rounded hover:bg-police-light">Search</button>
      </div>
      <DataTable />
    </div>
  );
}
