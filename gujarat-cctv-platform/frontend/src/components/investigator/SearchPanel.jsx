import React from 'react';
export default function SearchPanel() {
  return (
    <div className="flex flex-col gap-4">
      <input type="text" placeholder="Entity ID or Description" className="border p-2 rounded" />
      <button className="bg-police-blue text-white p-2 rounded">Search Entities</button>
      <div className="mt-4 border-t pt-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">Search Guidelines</h3>
        <p className="text-xs text-gray-500 leading-relaxed">
          Enter a vehicle license plate, person attribute, or camera identifier to query live observations from across Gujarat.
        </p>
      </div>
    </div>
  );
}
