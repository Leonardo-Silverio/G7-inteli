import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { PageHeader } from '../components/PageHeader';
import { Card, CardBody, CardHeader } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { EmptyState } from '../components/EmptyState';
import { Badge } from '../components/Badge';
import { formatDateShort, getStatusProjetoLabel, getStatusProjetoColor } from '../utils/formatters';
import type { ProjetoResponse } from '../types';
import { isDemoMode, demoProjetos } from '../demo/demoData';

export function VerticalPortal() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [projetos, setProjetos] = useState<ProjetoResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const demoMode = isDemoMode();

  const fetchProjetos = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get<{ items: ProjetoResponse[]; total: number }>('/projetos', {
        params: { page_size: 100 },
      });
      setProjetos(res.data.items);
    } catch (err: unknown) {
      if (demoMode) {
        setProjetos(demoProjetos);
        setError('');
      } else if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Erro ao carregar projetos');
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjetos(); }, []);

  return (
    <div>
      <PageHeader
        title={`Olá, ${currentUser?.email?.split('@')[0] || 'Usuário'}`}
        subtitle={currentUser?.vertical_id ? `Vertical: ${currentUser.vertical_id.slice(0, 8)}...` : undefined}
        action={
          <Button onClick={() => navigate('/projetos/novo')}>
            <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Novo Projeto
          </Button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Total de Projetos</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{projetos.length}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Em Andamento</p>
            <p className="text-2xl font-bold text-azul-600 mt-1">
              {projetos.filter((p) => !['LANCADO', 'ENCERRADO'].includes(p.status)).length}
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Concluídos</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">
              {projetos.filter((p) => ['LANCADO', 'ENCERRADO'].includes(p.status)).length}
            </p>
          </CardBody>
        </Card>
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error} onRetry={fetchProjetos} />}

      {!loading && !error && projetos.length === 0 && (
        <EmptyState
          title="Nenhum projeto encontrado"
          description="Crie seu primeiro projeto para começar."
          action={{ label: 'Criar Projeto', onClick: () => navigate('/projetos/novo') }}
        />
      )}

      {!loading && !error && projetos.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="font-semibold text-gray-900">Projetos Recentes</h3>
          </CardHeader>
          <CardBody className="p-0">
            <div className="divide-y divide-gray-100">
              {projetos.slice(0, 10).map((projeto) => (
                <div
                  key={projeto.id}
                  onClick={() => navigate(`/projetos/${projeto.id}`)}
                  className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{projeto.titulo}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {formatDateShort(projeto.created_at)} • {projeto.descricao?.slice(0, 80)}{projeto.descricao && projeto.descricao.length > 80 ? '...' : ''}
                    </p>
                  </div>
                  <Badge className={getStatusProjetoColor(projeto.status)}>
                    {getStatusProjetoLabel(projeto.status)}
                  </Badge>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
