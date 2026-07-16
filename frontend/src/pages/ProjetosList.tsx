import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { PageHeader } from '../components/PageHeader';
import { Card, CardBody } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { EmptyState } from '../components/EmptyState';
import { Badge } from '../components/Badge';
import { formatDateShort, getStatusProjetoLabel, getStatusProjetoColor } from '../utils/formatters';
import { PapelUsuario, StatusProjeto } from '../types';
import type { ProjetoResponse } from '../types';
import { isDemoMode, demoProjetos } from '../demo/demoData';

export function ProjetosList() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [projetos, setProjetos] = useState<ProjetoResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const demoMode = isDemoMode();
  const canCreate = currentUser?.papel === PapelUsuario.VERTICAL && !demoMode;
  const isReadOnly = currentUser?.papel === PapelUsuario.LIDERANCA;

  const fetchProjetos = async () => {
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string | number> = { page_size: 100 };
      if (search) params.search = search;
      if (filterStatus) params.status = filterStatus;
      const res = await api.get<{ items: ProjetoResponse[]; total: number }>('/projetos', { params });
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
        title="Projetos"
        subtitle={isReadOnly ? 'Acesso somente leitura' : undefined}
        action={
          canCreate && !demoMode ? (
            <Button onClick={() => navigate('/projetos/novo')}>
              <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Novo Projeto
            </Button>
          ) : undefined
        }
      />

      <div className="flex gap-3 mb-6">
        <div className="flex-1">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar projetos..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
        >
          <option value="">Todos os status</option>
          {Object.values(StatusProjeto).map((s) => (
            <option key={s} value={s}>{getStatusProjetoLabel(s)}</option>
          ))}
        </select>
        <Button variant="secondary" onClick={fetchProjetos}>Buscar</Button>
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error} onRetry={fetchProjetos} />}

      {!loading && !error && projetos.length === 0 && (
        <EmptyState
          title="Nenhum projeto encontrado"
          description={canCreate && !demoMode ? 'Crie seu primeiro projeto para começar.' : 'Não há projetos disponíveis.'}
          action={canCreate && !demoMode ? { label: 'Criar Projeto', onClick: () => navigate('/projetos/novo') } : undefined}
        />
      )}

      {!loading && !error && projetos.length > 0 && (
        <div className="grid gap-4">
          {projetos.map((projeto) => (
            <Card
              key={projeto.id}
              onClick={() => navigate(`/projetos/${projeto.id}`)}
              className="cursor-pointer hover:shadow-md transition-shadow"
            >
              <CardBody>
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <h3 className="text-base font-semibold text-gray-900 truncate">{projeto.titulo}</h3>
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                      {projeto.descricao || 'Sem descrição'}
                    </p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                      <span>{formatDateShort(projeto.created_at)}</span>
                      <span>Vertical: {projeto.vertical_id.slice(0, 8)}...</span>
                    </div>
                  </div>
                  <Badge className={`ml-4 ${getStatusProjetoColor(projeto.status)}`}>
                    {getStatusProjetoLabel(projeto.status)}
                  </Badge>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
