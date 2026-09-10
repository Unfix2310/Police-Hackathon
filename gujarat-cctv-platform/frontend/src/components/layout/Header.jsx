import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { LogOut, Bell, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-4">
        <span className="font-semibold text-gray-700 capitalize">{user?.role} Mode</span>
      </div>
      <div className="flex items-center gap-6">
        <button className="text-gray-500 hover:text-police-blue relative" title="System Notifications">
          <Bell size={20} />
        </button>
        <div className="flex items-center gap-2 text-sm text-gray-700 border-l pl-6 border-gray-200">
          <User size={16} />
          <span>{user?.username}</span>
          <button onClick={handleLogout} className="ml-4 text-gray-500 hover:text-red-500" title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  );
}
