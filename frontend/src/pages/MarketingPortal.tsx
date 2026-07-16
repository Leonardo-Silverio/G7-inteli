import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { PageHeader } from '../components/PageHeader';
import { Card, CardBody, CardHeader } from '../components/Card';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { EmptyState } from '../components/EmptyState';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import { ScoreCard } from '../components/ScoreCard';
import { formatDateShort, getStatusProjetoLabel, getStatusProjetoColor, getFarolLabel, getFarolColor } from '../utils/formatters';
import {
  PapelUsuario,
  StatusProjeto,
  ClassificacaoFarol,
  type ProjetoResponse,
  type AvaliacaoCheckpointResponse,
} from '../types';
import { isDemoMode, demoProjetos, demoAvaliacaoHistory, demoCheckpoints } from '../demo/demoData';

interface ProjetoComAvaliacao extends ProjetoResponse {
  avaliacao?: AvaliacaoCheckpointResponse;
  prioridade: number;
}

export function MarketingPortal() {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser } = useAuth();
  const [projetos, setProjetos] = useState<ProjetoResponse[]>([]);
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoCheckpointResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtroVertical, setFiltroVertical] = useState('');
  const [filtroClassificacao, setFiltroClassificacao] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('');
  const [busca, setBusca] = useState('');

  const demoMode = isDemoMode();
  const isMarketing = currentUser?.papel === PapelUsuario.MARKETING || demoMode;

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      if (demoMode) {
        setProjetos(demoProjetos);
        setAvaliacoes(demoAvaliacaoHistory.items);
        setError('');
      } else {
        const [projRes, avalRes] = await Promise.all([
          api.get<{ items: ProjetoResponse[]; total: number }>('/projetos', { params: { page_size: 100 } }),
          api.get<AvaliacaoCheckpointResponse[]>('/avaliacoes', { params: { page_size: 200 } }),
        ]);
        setProjetos(projRes.data.items);
        setAvaliacoes(avalRes.data);
      }
    } catch (err: unknown) {
      if (demoMode) {
        setProjetos(demoProjetos);
        setAvaliacoes(demoAvaliacaoHistory.items);
        setError('');
      } else if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 401) {
          setError('Sessão expirada. Faça login novamente.');
        } else {
          setError(axiosErr.response?.data?.detail || 'Erro ao carregar dados');
        }
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const avaliacoesPorProjeto = useMemo(() => {
    const map = new Map<string, AvaliacaoCheckpointResponse>();
    avaliacoes.forEach((a) => {
      const checkpoint = demoCheckpoints.find((c) => c.id === a.checkpoint_id);
      if (checkpoint) {
        const existing = map.get(checkpoint.projeto_id);
        if (!existing || new Date(a.evaluated_at) > new Date(existing.evaluated_at)) {
          map.set(checkpoint.projeto_id, a);
        }
      }
    });
    return map;
  }, [avaliacoes]);

  const projetosComAvaliacao = useMemo((): ProjetoComAvaliacao[] => {
    return projetos.map((projeto) => {
      const avaliacao = avaliacoesPorProjeto.get(projeto.id);
      let prioridade = 4;
      if (avaliacao) {
        switch (avaliacao.classificacao_farol) {
          case ClassificacaoFarol.PRIORIDADE_MAXIMA: prioridade = 1; break;
          case ClassificacaoFarol.VALE_INVESTIR_TEMPO: prioridade = 2; break;
          case ClassificacaoFarol.BAIXA_PRIORIDADE: prioridade = 3; break;
        }
      }
      return { ...projeto, avaliacao, prioridade };
    });
  }, [projetos, avaliacoesPorProjeto]);

  const projetosOrdenados = useMemo(() => {
    return [...projetosComAvaliacao].sort((a, b) => {
      if (a.prioridade !== b.prioridade) return a.prioridade - b.prioridade;
      const scorePotencialA = a.avaliacao?.score_potencial ?? -1;
      const scorePotencialB = b.avaliacao?.score_potencial ?? -1;
      if (scorePotencialA !== scorePotencialB) return scorePotencialB - scorePotencialA;
      const scoreAlinhamentoA = a.avaliacao?.score_alinhamento ?? -1;
      const scoreAlinhamentoB = b.avaliacao?.score_alinhamento ?? -1;
      if (scoreAlinhamentoA !== scoreAlinhamentoB) return scoreAlinhamentoB - scoreAlinhamentoA;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });
  }, [projetosComAvaliacao]);

  const projetosFiltrados = useMemo(() => {
    return projetosOrdenados.filter((p) => {
      if (filtroVertical && p.vertical_id !== filtroVertical) return false;
      if (filtroStatus && p.status !== filtroStatus) return false;
      if (filtroClassificacao) {
        const classif = p.avaliacao?.classificacao_farol ?? 'SEM_AVALIACAO';
        if (classif !== filtroClassificacao) return false;
      }
      if (busca) {
        const termo = busca.toLowerCase();
        if (!p.titulo.toLowerCase().includes(termo) &&
            !p.descricao?.toLowerCase().includes(termo) &&
            !p.vertical_id.toLowerCase().includes(termo)) {
          return false;
        }
      }
      return true;
    });
  }, [projetosOrdenados, filtroVertical, filtroClassificacao, filtroStatus, busca]);

  const verticais = useMemo(() => [...new Set(projetos.map((p) => p.vertical_id))].sort(), [projetos]);

  const stats = useMemo(() => {
    const total = projetosFiltrados.length;
    const max = projetosFiltrados.filter((p) => p.avaliacao?.classificacao_farol === ClassificacaoFarol.PRIORIDADE_MAXIMA).length;
    const vale = projetosFiltrados.filter((p) => p.avaliacao?.classificacao_farol === ClassificacaoFarol.VALE_INVESTIR_TEMPO).length;
    const baixa = projetosFiltrados.filter((p) => p.avaliacao?.classificacao_farol === ClassificacaoFarol.BAIXA_PRIORIDADE).length;
    return { total, max, vale, baixa };
  }, [projetosFiltrados]);

  if (isMarketing && location.pathname === '/projetos/novo') {
    navigate('/marketing', { replace: true });
    return null;
  }

  return (
    <div>
      <PageHeader
        title="Portal Marketing"
        subtitle="Triagem e priorização de projetos estratégicos"
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <div className="flex-1 min-w-[200px]">
          <select
            value={filtroVertical}
            onChange={(e) => setFiltroVertical(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
          >
            <option value="">Todas as Verticais</option>
            {verticais.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <select
            value={filtroClassificacao}
            onChange={(e) => setFiltroClassificacao(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
          >
            <option value="">Todas as Classificações</option>
            <option value={ClassificacaoFarol.PRIORIDADE_MAXIMA}>Prioridade Máxima</option>
            <option value={ClassificacaoFarol.VALE_INVESTIR_TEMPO}>Vale Investir Tempo</option>
            <option value={ClassificacaoFarol.BAIXA_PRIORIDADE}>Baixa Prioridade</option>
            <option value="SEM_AVALIACAO">Sem Avaliação</option>
          </select>
        </div>
        <div className="flex-1 min-w-[180px]">
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
          >
            <option value="">Todos os Status</option>
            {Object.values(StatusProjeto).map((s) => (
              <option key={s} value={s}>{getStatusProjetoLabel(s)}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por nome, descrição ou vertical..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
          />
        </div>
        <Button variant="secondary" onClick={() => { setFiltroVertical(''); setFiltroClassificacao(''); setFiltroStatus(''); setBusca(''); }}>
          Limpar
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Total de Projetos</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Prioridade Máxima</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{stats.max}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Vale Investir Tempo</p>
            <p className="text-2xl font-bold text-amber-600 mt-1">{stats.vale}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Baixa Prioridade</p>
            <p className="text-2xl font-bold text-gray-600 mt-1">{stats.baixa}</p>
          </CardBody>
        </Card>
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error} onRetry={fetchData} />}

      {!loading && !error && projetosFiltrados.length === 0 && (
        <EmptyState title="Nenhum projeto encontrado" description="Tente ajustar os filtros ou busca." />
      )}

      {!loading && !error && projetosFiltrados.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Projetos Priorizados ({projetosFiltrados.length})</h3>
              <span className="text-xs text-gray-400">Ordenados por prioridade decrescente</span>
            </div>
          </CardHeader>
          <CardBody className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Projeto</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">Vertical</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden lg:table-cell">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Classificação</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">Alinhamento</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">Potencial</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden lg:table-cell">Avaliação</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {projetosFiltrados.map((projeto) => (
                    <tr key={projeto.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/projetos/${projeto.id}`)}>
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 truncate max-w-xs">{projeto.titulo}</p>
                        <p className="text-xs text-gray-500 truncate max-w-xs">{projeto.descricao?.slice(0, 60) || 'Sem descrição'}</p>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell text-gray-600">{projeto.vertical_id}</td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <Badge className={getStatusProjetoColor(projeto.status)}>{getStatusProjetoLabel(projeto.status)}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getFarolColor(projeto.avaliacao?.classificacao_farol)}`}>
{getFarolLabel(projeto.avaliacao?.classificacao_farol)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right hidden md:table-cell font-mono text-gray-900">
                        {projeto.avaliacao?.score_alinhamento ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right hidden md:table-cell font-mono text-gray-900">
                        {projeto.avaliacao?.score_potencial ?? '—'}
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell text-gray-500">
                        {projeto.avaliacao ? formatDateShort(projeto.avaliacao.evaluated_at) : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
<Button variant="secondary" className="px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); navigate(`/projetos/${projeto.id}`); }}>
                          Ver detalhes
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="hidden lg:block lg:hidden">
              {projetosFiltrados.map((projeto) => (
                <div key={projeto.id} className="p-4 border-b border-gray-100 last:border-0 hover:bg-gray-50" onClick={() => navigate(`/projetos/${projeto.id}`)}>
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{projeto.titulo}</p>
                      <p className="text-xs text-gray-500 mt-0.5 truncate">{projeto.descricao?.slice(0, 80) || 'Sem descrição'}</p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getFarolColor(projeto.avaliacao?.classificacao_farol)} shrink-0`}>
                      {getFarolLabel(projeto.avaliacao?.classificacao_farol)}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-2">
                    <span>{projeto.vertical_id}</span>
                    <Badge className={getStatusProjetoColor(projeto.status)}>{getStatusProjetoLabel(projeto.status)}</Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <ScoreCard label="Alinhamento" score={projeto.avaliacao?.score_alinhamento ?? 0} showLabel={false} />
                    </div>
                    <div className="flex items-center gap-1">
                      <ScoreCard label="Potencial" score={projeto.avaliacao?.score_potencial ?? 0} showLabel={false} />
                    </div>
                    <span className="text-gray-400 ml-auto">
                      {projeto.avaliacao ? formatDateShort(projeto.avaliacao.evaluated_at) : 'Sem avaliação'}
                    </span>
                    <Button variant="secondary" className="px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); navigate(`/projetos/${projeto.id}`); }}>
                      Ver detalhes
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}