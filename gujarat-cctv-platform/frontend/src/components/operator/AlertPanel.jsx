import React, { useState, useEffect } from 'react';
import { ShieldCheck, BellOff, AlertTriangle, Clock, MapPin, CheckCircle } from 'lucide-react';
import api from '../../services/api';
import { useAlerts } from '../../hooks/useAlerts';

export default function AlertPanel() {
  const [alerts, setAlerts] = useState([]);
  const wsAlerts = useAlerts();

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await api.get('/alerts');
        if (Array.isArray(res.data)) {
          setAlerts(res.data);
        }
      } catch {
        setAlerts([]);
      }
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  // Merge: prepend live WS alerts, deduplicate by alert_id
  const allAlerts = React.useMemo(() => {
    const seen = new Set();
    const merged = [];
    for (const a of [...(wsAlerts || []), ...alerts]) {
      const id = a.alert_id || a.id;
      if (id && !seen.has(id)) {
        seen.add(id);
        merged.push(a);
      }
    }
    return merged.slice(0, 50);
  }, [wsAlerts, alerts]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.patch(`/alerts/${alertId}/acknowledge`, { comment: 'Acknowledged from dashboard' });
      setAlerts(prev => prev.filter(a => (a.alert_id || a.id) !== alertId));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  if (!allAlerts || allAlerts.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-500 border border-dashed border-slate-200 rounded-lg bg-slate-50/50">
        <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mb-3 shadow-sm">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-800">No Active Alerts</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-[200px]">
          All 30 camera feeds operating normally. Threat detection active.
        </p>
        <div className="mt-4 flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          Live Perception Scanning
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto space-y-3 pr-1">
      {allAlerts.map((alert, idx) => {
        const priority = alert.priority || 'P3';
        const isP1 = priority === 'P1';
        const isP2 = priority === 'P2';
        return (
          <div
            key={alert.alert_id || alert.id || idx}
            className={`p-3 rounded-lg border shadow-sm transition-all ${
              isP1 ? 'bg-red-50 border-red-200' : isP2 ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-1.5">
                <AlertTriangle className={`w-4 h-4 ${isP1 ? 'text-red-600' : 'text-amber-600'}`} />
                <span className="font-semibold text-xs text-slate-900">
                  {alert.alert_type || 'Alert'}
                </span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isP1 ? 'bg-red-200 text-red-800' : 'bg-amber-200 text-amber-800'}`}>
                  {priority}
                </span>
              </div>
              <span className="text-[10px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'Just now'}
              </span>
            </div>
            <p className="text-xs text-slate-700 mt-1.5">{alert.message}</p>
            {alert.camera_id && (
              <div className="mt-1 flex items-center gap-1 text-[10px] text-slate-500 font-mono">
                <MapPin className="w-3 h-3 text-slate-400" />
                <span>Camera: {alert.camera_id}</span>
              </div>
            )}
            <div className="mt-2 flex justify-end">
              <button
                onClick={() => handleAcknowledge(alert.alert_id || alert.id)}
                className="flex items-center gap-1 text-[11px] bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded transition-colors"
              >
                <CheckCircle className="w-3 h-3" />
                Acknowledge
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
