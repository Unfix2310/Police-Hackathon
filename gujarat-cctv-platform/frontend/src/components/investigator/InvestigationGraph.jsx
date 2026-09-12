import React, { useState, useEffect } from 'react';
import api from '../../services/api';

export default function InvestigationGraph({ entityId }) {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (entityId) {
      setLoading(true);
      const endpoint = entityId.startsWith('P-') 
        ? `/graph/person/${entityId}` 
        : `/graph/vehicle/${entityId}`;
      
      api.get(endpoint)
        .then(res => {
          if (res.data) {
            setNodes(res.data.nodes || []);
            setLinks(res.data.edges || []);
          }
        })
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    } else {
      // Mock data
      setNodes([
        { id: 'P-001', type: 'person' },
        { id: 'V-WHITE-SED-01', type: 'vehicle' },
        { id: 'cam01', type: 'camera' }
      ]);
      setLinks([
        { source: 'P-001', target: 'V-WHITE-SED-01' },
        { source: 'V-WHITE-SED-01', target: 'cam01' },
        { source: 'cam01', target: 'P-001' }
      ]);
    }
  }, [entityId]);

  if (loading) {
    return <div className="h-full w-full bg-gray-50 flex items-center justify-center border rounded text-slate-500">Loading graph...</div>;
  }

  // Simple circular layout
  const width = 800;
  const height = 500;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;

  const positionedNodes = nodes.map((node, i) => {
    const angle = (i / (nodes.length || 1)) * 2 * Math.PI - Math.PI / 2;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  });

  const nodeMap = {};
  positionedNodes.forEach(n => { nodeMap[n.id] = n; });

  return (
    <div className="h-full w-full bg-gray-50 flex items-center justify-center border rounded overflow-hidden">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full max-w-full max-h-full">
        <g>
          {links.map((link, i) => {
            const source = typeof link.source === 'object' ? link.source : nodeMap[link.source];
            const target = typeof link.target === 'object' ? link.target : nodeMap[link.target];
            if (!source || !target) return null;
            return (
              <line
                key={i}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="#94a3b8"
                strokeWidth="2"
              />
            );
          })}
          {positionedNodes.map(node => (
            <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
              <circle
                r="24"
                fill={
                  ((node.type || node.entity_type || '').toLowerCase() === 'vehicle' || (node.id && node.id.startsWith('V-'))) ? '#3b82f6' : // blue
                  ((node.type || node.entity_type || '').toLowerCase() === 'person' || (node.id && node.id.startsWith('P-'))) ? '#22c55e' : // green
                  ((node.type || node.entity_type || '').toLowerCase() === 'camera' || (node.id && node.id.startsWith('cam'))) ? '#f97316' : '#64748b' // orange
                }
                stroke="#fff"
                strokeWidth="3"
                className="shadow-sm"
              />
              <text
                dy="40"
                textAnchor="middle"
                className="text-xs font-semibold fill-slate-700 pointer-events-none"
              >
                {node.id}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}
