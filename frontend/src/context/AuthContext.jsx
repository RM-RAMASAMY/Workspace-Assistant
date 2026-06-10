import React, { createContext, useState, useEffect, useContext } from 'react';
import { apiCall } from '../utils/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await apiCall('/auth/me', 'GET', null, token);
          setUser(userData);
        } catch (error) {
          console.error("Failed to load user:", error);
          setToken(null);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    loadUser();
  }, [token]);

  const login = async (email, password) => {
    const data = await apiCall('/auth/login', 'POST', { email, password });
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
    const userData = await apiCall('/auth/me', 'GET', null, data.access_token);
    setUser(userData);
  };

  const register = async (email, name, password) => {
    await apiCall('/auth/register', 'POST', { email, name, password });
    await login(email, password);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
