import React from 'react';
export default function StatusIndicator({ active }) {
  return <span className={`w-3 h-3 rounded-full inline-block ${active ? 'bg-green-500' : 'bg-red-500'}`}></span>;
}
