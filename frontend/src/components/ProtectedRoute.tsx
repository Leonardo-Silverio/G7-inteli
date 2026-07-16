import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from './LoadingSpinner';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading, isDemo } = useAuth();

  if (loading) return <LoadingSpinner message="Verificando autenticação..." />;
  if (!isAuthenticated && !isDemo) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
