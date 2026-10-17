import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await authService.getCurrentUser();
        if (response.data.success && response.data.data.user) {
          setUser(response.data.data.user);
        }
      } catch (err) {
        // Not logged in or session expired — expected, not an error
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    checkSession();
  }, []);

  // Returns { success: true } or { success: false, error: string }
  // Pages manage their own error display state
  const login = async (email, password) => {
    try {
      const response = await authService.login({ email, password });
      if (response.data.success) {
        setUser(response.data.data.user);
        return { success: true };
      }
      return { success: false, error: 'Login failed.' };
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Failed to login. Please try again.';
      return { success: false, error: msg };
    }
  };

  // Returns { success: true } or { success: false, error: string }
  const register = async (userData) => {
    try {
      // Registration is household-only. Keep the fixed account type in the
      // request for API deployments that still require this field.
      const response = await authService.register({ ...userData, user_type: 'household' });
      if (response.data.success) {
        setUser(response.data.data.user);
        return { success: true };
      }
      return { success: false, error: 'Registration failed.' };
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Failed to register. Please try again.';
      return { success: false, error: msg };
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
