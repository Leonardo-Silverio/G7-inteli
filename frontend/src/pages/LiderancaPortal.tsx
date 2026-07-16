import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { PageHeader } from '../components/PageHeader';
import { Card, CardBody, CardHeader } from '../components/Card';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { EmptyState } from '../components/EmptyState';
import { Badge } from '../components/Badge';
import { formatDateShort, getStatusProjetoLabel, getStatusProjetoColor } from '../utils/formatters';
import type { ProjetoResponse } from '../types';

export function LiderancaPortal() {
  const navigate = useNavigate();
  const [projetos, setProjetos] = useState<ProjetoResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchProjetos = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get<{ items: ProjetoResponse[]; total: number }>('/projetos', {
        params: { page_size: 100 },
      });
      setProjetos(res.data.items);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
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
        title="Portal Liderança"
        subtitle="Acompanhamento de projetos (acesso somente leitura)"
      />

      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error} onRetry={fetchProjetos} />}

      {!loading && !error && projetos.length === 0 && (
        <EmptyState title="Nenhum projeto encontrado" description="Não há projetos disponíveis no momento." />
      )}

      {!loading && !error && projetos.length > 0 && (
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Projetos</h3></CardHeader>
          <CardBody className="p-0">
            <div className="divide-y divide-gray-100">
              {projetos.map((projeto) => (
                <div
                  key={projeto.id}
                  onClick={() => navigate(`/projetos/${projeto.id}`)}
                  className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{projeto.titulo}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{formatDateShort(projeto.created_at)}</p>
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
