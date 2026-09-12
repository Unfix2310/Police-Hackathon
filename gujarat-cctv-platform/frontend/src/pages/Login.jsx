import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ShieldAlert } from 'lucide-react';

export default function Login() {
  const [role, setRole] = useState('admin');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, error } = useAuth();
  const navigate = useNavigate();

  const ROLE_MAP = {
    operator: { username: 'GJ-OPR-001', password: 'demo123', route: '/operator' },
    investigator: { username: 'GJ-INV-001', password: 'demo123', route: '/investigator' },
    command: { username: 'GJ-CMD-001', password: 'demo123', route: '/command' },
    admin: { username: 'GJ-ADM-001', password: 'demo123', route: '/command' },
    anpr: { username: 'GJ-ADM-001', password: 'demo123', route: '/anpr-test' },
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    const target = ROLE_MAP[role] || ROLE_MAP.admin;
    try {
      await login(target.username, target.password);
      navigate(target.route);
    } catch (err) {
      console.error('Login failed', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
        <div className="text-center mb-8">
          <ShieldAlert size={48} className="mx-auto text-police-blue mb-4" />
          <h1 className="text-2xl font-bold text-gray-900">Gujarat Police</h1>
          <p className="text-gray-500">CCTV Intelligence Platform</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Role for Demo</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-police-blue focus:ring-police-blue p-2 border"
            >
              <option value="operator">Operator Console</option>
              <option value="investigator">Investigator Workspace</option>
              <option value="command">Command Dashboard</option>
              <option value="admin">Administrator</option>
              <option value="anpr">ANPR Test Lab (Isolated)</option>
            </select>
          </div>
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md">
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-police-blue hover:bg-police-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-police-blue disabled:opacity-50"
          >
            {isSubmitting ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
