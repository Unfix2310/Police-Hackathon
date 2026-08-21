import React from 'react';
export default function ConfidenceBadge({ score }) {
  const color = score > 0.8 ? 'bg-green-100 text-green-800' : score > 0.5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';
  return <span className={`px-2 py-1 rounded text-xs font-semibold ${color}`}>{(score * 100).toFixed(0)}%</span>;
}
