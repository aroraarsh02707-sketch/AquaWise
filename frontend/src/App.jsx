import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';

import './index.css';

// A temporary stub for the dashboard to verify authentication
const DashboardStub = () => {
  const { user, logout } = useAuth();
  
  return (
    <div className="dashboard-stub">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>AquaWise Dashboard</h2>
        <button onClick={logout} className="logout-btn">Log Out</button>
      </div>
      <p>Welcome back, <strong>{user?.name}</strong>!</p>
      <p>Your account type: <span style={{ textTransform: 'capitalize', color: 'var(--conservation-green)', fontWeight: 'bold' }}>{user?.user_type}</span></p>
      <p style={{ marginTop: '2rem', color: '#64748b' }}>
        (This is a protected route. The full dashboard will be implemented in a future phase.)
      </p>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardStub />
              </ProtectedRoute>
            } 
          />
          
          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
