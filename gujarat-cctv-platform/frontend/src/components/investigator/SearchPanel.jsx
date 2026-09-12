import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

export default function SearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!query) return;
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

  return (
    <div className="flex flex-col gap-4 h-full">
      <input 
        type="text" 
        placeholder="Entity ID or Description" 
        className="border p-2 rounded" 
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
      />
      <button 
        className="bg-police-blue text-white p-2 rounded disabled:opacity-50"
        onClick={handleSearch}
        disabled={loading}
      >
        {loading ? 'Searching...' : 'Search Entities'}
      </button>

      {results.length > 0 && (
        <div className="flex flex-col gap-2 mt-2 max-h-96 overflow-y-auto pr-1">
          {results.map(r => (
            <div 
              key={r.id} 
              className="border rounded p-3 cursor-pointer hover:bg-gray-50 text-sm shadow-sm transition-shadow hover:shadow-md"
              onClick={() => navigate(`/trajectory?entityType=${r.type.toLowerCase()}&entityId=${r.id}`)}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${r.type === 'VEHICLE' ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'}`}>
                  {r.type}
                </span>
                <span className="text-xs text-gray-500 whitespace-nowrap ml-2">{new Date(r.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="font-medium text-gray-800 mb-2 line-clamp-2">{r.description}</div>
              <div className="flex justify-between items-center mt-1 border-t pt-2">
                <span className="text-xs text-gray-600 truncate mr-2" title={r.camera_name}>{r.camera_name}</span>
                <span className="text-xs font-medium text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded">{(r.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-auto border-t pt-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">Search Guidelines</h3>
        <p className="text-xs text-gray-500 leading-relaxed">
          Enter a vehicle license plate, person attribute, or camera identifier to query live observations from across Gujarat.
        </p>
      </div>
    </div>
  );
}
