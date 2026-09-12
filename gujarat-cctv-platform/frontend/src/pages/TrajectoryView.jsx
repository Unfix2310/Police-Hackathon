import React, { useState, useEffect } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import TrajectoryMap from '../components/investigator/TrajectoryMap';
import TrajectoryTimeline from '../components/investigator/TrajectoryTimeline';
import api from '../services/api';
import { Loader2, AlertTriangle } from 'lucide-react';

export default function TrajectoryView() {
  const [searchParams] = useSearchParams();
  const params = useParams();
  const entityType = params.entityType || searchParams.get('entityType') || 'vehicle';
  const entityId = params.entityId || searchParams.get('entityId') || '';
  const [trajectory, setTrajectory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!entityId) return;
    setLoading(true);
    setError(null);
    api.get(`/trajectory/${entityType}/${entityId}`)
      .then(res => {
        setTrajectory(res.data);
      })
      .catch(err => {
        setError(err.response?.data?.detail || 'Failed to load trajectory');
      })
      .finally(() => setLoading(false));
  }, [entityType, entityId]);

  const steps = trajectory?.trajectory?.map((point, idx) => ({
    camera_id: point.camera_id,
    camera_name: point.camera_id,
    timestamp: point.timestamp,
    location: point.camera_id,
    speed_from_previous: point.speed_from_previous,
    lat: point.lat,
    lng: point.lng,
  })) || [];

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-police-blue">Entity Trajectory Analysis</h2>
          {entityId && (
            <p className="text-sm text-slate-500 mt-1">
              {entityType.toUpperCase()}: <span className="font-mono font-semibold text-slate-700">{entityId}</span>
              {trajectory && (
                <span className="ml-3 text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                  {steps.length} sightings · Feasibility: {((trajectory.feasibility_score || 0) * 100).toFixed(0)}%
                </span>
              )}
            </p>
          )}
        </div>
        <button className="bg-saffron text-white px-4 py-2 rounded text-sm">Export Evidence Package</button>
      </div>

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-2 text-slate-500">Loading trajectory...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 text-sm">{error}</span>
        </div>
      )}

      {!loading && !error && (
        <div className="flex-1 flex gap-4">
          <div className="w-2/3 bg-white p-4 rounded-lg shadow">
            <div className="h-full">
              <TrajectoryMap steps={steps} anomalies={trajectory?.anomalies || []} />
            </div>
          </div>
          <div className="w-1/3 bg-white p-4 rounded-lg shadow overflow-y-auto">
            <TrajectoryTimeline steps={steps} />
          </div>
        </div>
      )}
    </div>
  );
}
