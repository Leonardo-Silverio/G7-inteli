import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { setToken, clearToken, getToken } from '../api/client';
import type { CurrentUser } from '../types';
import { isDemoMode, demoUser } from '../demo/demoData';

interface AuthContextType {
  token: string | null;
  currentUser: CurrentUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  isDemo: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(getToken());
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const demoMode = isDemoMode();
  const navigate = useNavigate();

  const fetchUser = useCallback(async () => {
    if (demoMode) {
      setCurrentUser(demoUser);
      setLoading(false);
      return;
    }
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      const res = await api.get<CurrentUser>('/auth/me');
      setCurrentUser(res.data);
    } catch {
      clearToken();
      setTokenState(null);
      setCurrentUser(null);
    } finally {
      setLoading(false);
    }
  }, [demoMode]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(async (email: string, senha: string) => {
    if (demoMode) {
      setCurrentUser(demoUser);
      return;
    }
    const res = await api.post<{ access_token: string; token_type: string }>('/auth/login', {
      email,
      senha,
    });
    const t = res.data.access_token;
    setToken(t);
    setTokenState(t);
    const userRes = await api.get<CurrentUser>('/auth/me');
    setCurrentUser(userRes.data);
  }, [demoMode]);

  const logout = useCallback(() => {
    if (demoMode) {
      // In demo mode, stay in demo mode and redirect to vertical
      navigate('/vertical', { replace: true });
      return;
    }
    clearToken();
    setTokenState(null);
    setCurrentUser(null);
    navigate('/login', { replace: true });
  }, [demoMode, navigate]);

  return (
    <AuthContext.Provider
      value={{ token, currentUser, loading, isAuthenticated: demoMode || (!!token && !!currentUser), isDemo: demoMode, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
