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
import { formatDateShort, getStatusProjetoColor, getStatusProjetoLabel } from '../utils/formatters';
import { PapelUsuario } from '../types';
import type { ProjetoResponse } from '../types';
import { isDemoMode, demoProjetos } from '../demo/demoData';

interface DashboardStats {
  totalProjetos: number;
  totalCheckpoints: number;
  totalAvaliacoes: number;
  projetosEmAndamento: number;
  projetosConcluidos: number;
}

export function Dashboard() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [projetos, setProjetos] = useState<ProjetoResponse[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalProjetos: 0,
    totalCheckpoints: 0,
    totalAvaliacoes: 0,
    projetosEmAndamento: 0,
    projetosConcluidos: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [fetchingStats, setFetchingStats] = useState(false);

  const demoMode = isDemoMode();
  const canCreate = currentUser?.papel === PapelUsuario.VERTICAL;
  const isReadOnly = currentUser?.papel === PapelUsuario.LIDERANCA || currentUser?.papel === PapelUsuario.MARKETING;

  const fetchProjetos = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get<{ items: ProjetoResponse[]; total: number }>('/projetos', {
        params: { page_size: 100 },
      });
      const items = res.data.items;
      setProjetos(items);

      setStats({
        totalProjetos: items.length,
        totalCheckpoints: 0,
        totalAvaliacoes: 0,
        projetosEmAndamento: items.filter((p) => !['LANCADO', 'ENCERRADO'].includes(p.status)).length,
        projetosConcluidos: items.filter((p) => ['LANCADO', 'ENCERRADO'].includes(p.status)).length,
      });

      await fetchStatsForProjects(items);
    } catch (err: unknown) {
      if (demoMode) {
        // Use demo data in demo mode
        setProjetos(demoProjetos);
        setStats({
          totalProjetos: demoProjetos.length,
          totalCheckpoints: 6,
          totalAvaliacoes: 2,
          projetosEmAndamento: demoProjetos.filter((p) => !['LANCADO', 'ENCERRADO'].includes(p.status)).length,
          projetosConcluidos: demoProjetos.filter((p) => ['LANCADO', 'ENCERRADO'].includes(p.status)).length,
        });
        setError('');
      } else if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Erro ao carregar dashboard');
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStatsForProjects = async (items: ProjetoResponse[]) => {
    if (items.length === 0) return;
    setFetchingStats(true);
    try {
      let totalCheckpoints = 0;
      let totalAvaliacoes = 0;

      for (const projeto of items) {
        try {
          const cpRes = await api.get<{ items: { status: string }[]; total: number }>(
            `/projetos/${projeto.id}/checkpoints`
          );
          totalCheckpoints += cpRes.data.items.length;

          for (const cp of cpRes.data.items) {
            if (cp.status === 'CONCLUIDO') {
              try {
                const avalRes = await api.get<{ avaliacao: { id: string } | null; total_historico: number }>(
                  `/projetos/${projeto.id}/checkpoints/IDEACAO/avaliacao`
                );
                if (avalRes.data.avaliacao) totalAvaliacoes += avalRes.data.total_historico;
              } catch {
                // ignore
              }
            }
          }
        } catch {
          // ignore individual project errors
        }
      }

      setStats((prev) => ({
        ...prev,
        totalCheckpoints,
        totalAvaliacoes,
      }));
    } finally {
      setFetchingStats(false);
    }
  };

  useEffect(() => {
    fetchProjetos();
  }, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={isReadOnly ? 'Acesso somente leitura' : undefined}
        action={
          canCreate ? (
            <Button onClick={() => navigate('/projetos/novo')}>
              <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Novo Projeto
            </Button>
          ) : undefined
        }
      />

      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error} onRetry={fetchProjetos} />}

      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardBody>
                <p className="text-sm text-gray-500">Total de Projetos</p>
                <p className="mt-1 text-3xl font-bold text-gray-900">{stats.totalProjetos}</p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <p className="text-sm text-gray-500">Checkpoints</p>
                <p className="mt-1 text-3xl font-bold text-azul-600">{stats.totalCheckpoints}</p>
                {fetchingStats && <p className="mt-1 text-xs text-gray-400">Atualizando...</p>}
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <p className="text-sm text-gray-500">Avaliações Realizadas</p>
                <p className="mt-1 text-3xl font-bold text-emerald-600">{stats.totalAvaliacoes}</p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <p className="text-sm text-gray-500">Projetos em Andamento</p>
                <p className="mt-1 text-3xl font-bold text-amber-600">{stats.projetosEmAndamento}</p>
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <h3 className="font-semibold text-gray-900">Projetos Recentes</h3>
            </CardHeader>
            <CardBody className="p-0">
              {projetos.length === 0 ? (
                <EmptyState
                  title="Nenhum projeto encontrado"
                  description={canCreate ? 'Crie seu primeiro projeto para começar.' : 'Não há projetos disponíveis.'}
                  action={canCreate ? { label: 'Criar Projeto', onClick: () => navigate('/projetos/novo') } : undefined}
                />
              ) : (
                <div className="divide-y divide-gray-100">
                  {projetos.slice(0, 10).map((projeto) => (
                    <a
                      key={projeto.id}
                      href={`/projetos/${projeto.id}`}
                      className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">{projeto.titulo}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {formatDateShort(projeto.created_at)} • {projeto.descricao?.slice(0, 80) || 'Sem descrição'}
                        </p>
                      </div>
                      <Badge className={`ml-4 ${getStatusProjetoColor(projeto.status)}`}>
                        {getStatusProjetoLabel(projeto.status)}
                      </Badge>
                    </a>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}