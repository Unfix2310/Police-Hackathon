import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ShieldAlert } from 'lucide-react';

export default function Login() {
  const [role, setRole] = useState('operator');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    await login('demo_user', 'password', role);
    if (role === 'operator') navigate('/operator');
    else if (role === 'investigator') navigate('/investigator');
    else if (role === 'command') navigate('/command');
    else navigate('/operator');
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
            </select>
          </div>
          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-police-blue hover:bg-police-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-police-blue"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}
