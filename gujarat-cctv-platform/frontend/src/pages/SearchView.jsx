import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Search } from 'lucide-react';
import DataTable from '../components/shared/DataTable';
import api from '../services/api';

export default function SearchView() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await api.post('/search', { description: query });
      setResults(response.data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  const renderPlateBadge = (plate, type) => {
    if (type !== 'VEHICLE') {
      return <span className="text-gray-400 text-xs italic">N/A (Person)</span>;
    }
    if (!plate || plate === 'UNKNOWN' || plate === 'NO_PLATE') {
      return <span className="text-gray-400 text-xs italic">No Plate</span>;
    }
    if (plate === 'UNREADABLE' || plate === 'UNREADABLE_LOW_RES') {
      return (
        <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded text-xs font-medium">
          <AlertTriangle className="w-3 h-3 text-amber-600" />
          Unreadable
        </span>
      );
    }
    return (
      <div className="inline-flex items-center rounded border border-gray-400 bg-white shadow-xs overflow-hidden text-xs font-mono font-bold tracking-wider">
        <span className="bg-blue-700 text-white px-1.5 py-0.5 text-[9px] font-sans font-bold flex items-center">
          IND
        </span>
        <span className="px-2 py-0.5 text-gray-900 bg-white">
          {plate}
        </span>
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow h-full">
      <h2 className="text-2xl font-bold text-police-blue mb-6">Advanced Semantic Search</h2>
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="col-span-2 relative">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search by plate (e.g. GJ01AB1234), vehicle (e.g. Red car), or attribute..." 
            className="border p-2 pl-9 rounded w-full" 
          />
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
        </div>
        <input type="datetime-local" className="border p-2 rounded" />
        <button 
          onClick={handleSearch}
          className="bg-police-blue text-white p-2 rounded hover:bg-blue-800 disabled:opacity-50 font-medium"
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      {/* Replaced DataTable with a dynamic one */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-100 border-b text-gray-700 text-sm">
              <th className="p-3">Time</th>
              <th className="p-3">Camera</th>
              <th className="p-3">Location & Jurisdiction</th>
              <th className="p-3">Detection Type</th>
              <th className="p-3">Description</th>
              <th className="p-3">Plate / Details</th>
              <th className="p-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {results.length === 0 ? (
              <tr>
                <td colSpan="7" className="p-8 text-center text-gray-500">
                  {loading ? 'Searching...' : 'No live detections found yet.'}
                </td>
              </tr>
            ) : (
              results.map(r => (
                <tr 
                  key={r.id} 
                  className="border-b hover:bg-gray-50 text-sm cursor-pointer"
                  onClick={() => navigate(`/trajectory?entityType=${r.type.toLowerCase()}&entityId=${r.id}`)}
                >
                  <td className="p-3 whitespace-nowrap text-gray-600">{new Date(r.timestamp).toLocaleTimeString()}</td>
                  <td className="p-3">
                    <div className="font-semibold text-gray-800">{r.camera_name}</div>
                    <div className="text-xs text-gray-500 font-mono">{r.camera_id}</div>
                  </td>
                  <td className="p-3">
                    <div className="text-gray-800">{r.location}</div>
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded uppercase font-medium">{r.location_type || 'Intersection'}</span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${r.type === 'VEHICLE' ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'}`}>
                      {r.type}
                    </span>
                  </td>
                  <td className="p-3 font-medium text-gray-800">{r.description}</td>
                  <td className="p-3">
                    {renderPlateBadge(r.plate, r.type)}
                  </td>
                  <td className="p-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${(r.confidence * 100).toFixed(0)}%` }}></div>
                      </div>
                      <span className="text-xs font-semibold text-gray-700">{(r.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
