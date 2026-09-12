import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { MonitorPlay, Search, Activity, ShieldAlert, ScanLine } from 'lucide-react';

export default function Sidebar() {
  const { user } = useAuth();
  const role = user?.role;

  const links = [
    { to: '/operator', icon: <MonitorPlay />, label: 'Operator Console', roles: ['operator', 'admin'] },
    { to: '/investigator', icon: <Activity />, label: 'Investigator', roles: ['investigator', 'admin'] },
    { to: '/investigator/search', icon: <Search />, label: 'Advanced Search', roles: ['investigator', 'admin'] },
    { to: '/command', icon: <ShieldAlert />, label: 'Command Dashboard', roles: ['command', 'admin'] },
    { to: '/anpr-test', icon: <ScanLine />, label: 'ANPR Test Lab', roles: ['operator', 'investigator', 'command', 'admin'] },
  ];

  return (
    <div className="w-64 bg-police-blue text-white flex flex-col h-full">
      <div className="p-4 border-b border-police-light">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <ShieldAlert className="text-saffron" /> GCIP
        </h1>
        <p className="text-xs text-gray-300 mt-1">Gujarat CCTV Intelligence Platform</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {links.filter(link => link.roles.includes(role)).map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({isActive}) => `flex items-center gap-3 px-4 py-2 rounded-md transition-colors ${isActive ? 'bg-police-light text-saffron' : 'hover:bg-police-light/50'}`}
          >
            {link.icon}
            {link.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
