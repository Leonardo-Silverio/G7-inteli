import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthenticatedLayout } from './layouts/AuthenticatedLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { MarketingPortal } from './pages/MarketingPortal';
import { LiderancaPortal } from './pages/LiderancaPortal';
import { ProjetosList } from './pages/ProjetosList';
import { NovoProjeto } from './pages/NovoProjeto';
import { ProjetoDetail } from './pages/ProjetoDetail';
import { CheckpointForm } from './pages/CheckpointForm';
import { NotFound } from './pages/NotFound';
import { isDemoMode } from './demo/demoData';
import { PapelUsuario } from './types';

function NovoProjetoGuard() {
  const { currentUser } = useAuth();
  const location = useLocation();
  const demoMode = isDemoMode();
  const user = demoMode ? { papel: PapelUsuario.VERTICAL } : currentUser;

  if (user?.papel === PapelUsuario.MARKETING) {
    return <Navigate to="/marketing" replace state={{ from: location }} />;
  }
  return <NovoProjeto />;
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          element={
            <ProtectedRoute>
              <AuthenticatedLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/vertical" element={<Dashboard />} />
          <Route path="/marketing" element={<MarketingPortal />} />
          <Route path="/lideranca" element={<LiderancaPortal />} />
          <Route path="/projetos" element={<ProjetosList />} />
          <Route path="/projetos/novo" element={<NovoProjetoGuard />} />
          <Route path="/projetos/:projetoId" element={<ProjetoDetail />} />
          <Route path="/projetos/:projetoId/checkpoints/:tipo" element={<CheckpointForm />} />
        </Route>

        <Route path="/" element={<Navigate to={isDemoMode() ? '/vertical' : '/login'} replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
