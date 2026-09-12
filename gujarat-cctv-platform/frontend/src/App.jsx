import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import Login from './pages/Login';
import OperatorConsole from './pages/OperatorConsole';
import InvestigatorWorkspace from './pages/InvestigatorWorkspace';
import SearchView from './pages/SearchView';
import TrajectoryView from './pages/TrajectoryView';
import CommandDashboard from './pages/CommandDashboard';
import AnprTestLab from './pages/AnprTestLab';
import { AuthProvider, useAuth } from './hooks/useAuth';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/" />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" />;
  return <AppShell>{children}</AppShell>;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/operator" element={
        <ProtectedRoute allowedRoles={['operator', 'admin']}>
          <OperatorConsole />
        </ProtectedRoute>
      } />
      <Route path="/investigator" element={
        <ProtectedRoute allowedRoles={['investigator', 'admin']}>
          <InvestigatorWorkspace />
        </ProtectedRoute>
      } />
      <Route path="/investigator/search" element={
        <ProtectedRoute allowedRoles={['investigator', 'admin']}>
          <SearchView />
        </ProtectedRoute>
      } />
      <Route path="/trajectory" element={
        <ProtectedRoute allowedRoles={['investigator', 'admin', 'operator', 'command']}>
          <TrajectoryView />
        </ProtectedRoute>
      } />
      <Route path="/investigator/trajectory" element={
        <ProtectedRoute allowedRoles={['investigator', 'admin']}>
          <TrajectoryView />
        </ProtectedRoute>
      } />
      <Route path="/investigator/trajectory/:entityType/:entityId" element={
        <ProtectedRoute allowedRoles={['investigator', 'admin']}>
          <TrajectoryView />
        </ProtectedRoute>
      } />
      <Route path="/command" element={
        <ProtectedRoute allowedRoles={['command', 'admin']}>
          <CommandDashboard />
        </ProtectedRoute>
      } />
      <Route path="/anpr-test" element={
        <AppShell>
          <AnprTestLab />
        </AppShell>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
