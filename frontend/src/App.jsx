import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';

// Layouts & Pages
const AppLayout = lazy(() => import('./layouts/AppLayout.jsx'));
const Register = lazy(() => import('./pages/Register.jsx'));
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
const Assessment = lazy(() => import('./pages/Assessment.jsx'));
const Recommendations = lazy(() => import('./pages/Recommendations.jsx'));
const RecommendationsIndex = lazy(() => import('./pages/RecommendationsIndex.jsx'));
const Assistant = lazy(() => import('./pages/Assistant.jsx'));
const Profile = lazy(() => import('./pages/Profile.jsx'));

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<div className="loading-container" role="status" aria-live="polite"><div className="spinner" /><p>Loading AquaWise…</p></div>}>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Routes inside AppShell */}
            <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/assessment" element={<Assessment />} />
              <Route path="/recommendations" element={<RecommendationsIndex />} />
              <Route path="/recommendations/:id" element={<Recommendations />} />
              <Route path="/assistant" element={<Assistant />} />
              <Route path="/profile" element={<Profile />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
