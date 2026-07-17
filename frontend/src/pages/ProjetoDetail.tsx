import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardBody, CardHeader } from '../components/Card';
import { Tabs } from '../components/Tabs';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { ScoreCard, FarolBadge } from '../components/ScoreCard';
import { FeedbackSection } from '../components/FeedbackSection';
import {
  formatDate,
  getStatusProjetoLabel,
  getStatusProjetoColor,
  getStatusCheckpointLabel,
  getStatusCheckpointColor,
  formatFieldLabel,
  formatFieldValue,
} from '../utils/formatters';
import {
  PapelUsuario,
  StatusCheckpoint,
  TipoCheckpoint,
  type ProjetoResponse,
  type CheckpointResponse,
  type AvaliacaoLatestResponse,
  type AvaliacaoHistoryResponse,
  type ComparacaoAvaliacaoResponse,
  type EvolucaoAvaliacaoResponse,
} from '../types';
import { isDemoMode, demoProjetos, demoCheckpoints, demoAvaliacaoHistory, demoComparacao, demoEvolucao, demoMensagens, getDemoAvaliacaoForProject, type DemoMensagem } from '../demo/demoData';

type TabId = 'overview' | 'checkpoints' | 'avaliacao' | 'historico' | 'conversa';

type Tab = { id: TabId; label: string };

export function ProjetoDetail() {
  const { projetoId } = useParams<{ projetoId: string }>();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [projeto, setProjeto] = useState<ProjetoResponse | null>(null);
  const [checkpoints, setCheckpoints] = useState<CheckpointResponse[]>([]);
  const [avaliacao, setAvaliacao] = useState<AvaliacaoLatestResponse | null>(null);
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoHistoryResponse | null>(null);
  const [comparacao, setComparacao] = useState<ComparacaoAvaliacaoResponse | null>(null);
  const [evolucao, setEvolucao] = useState<EvolucaoAvaliacaoResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' | 'warning' | 'error' } | null>(null);

  const demoMode = isDemoMode();

  const showToast = (message: string, type: 'success' | 'info' | 'warning' | 'error' = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const isReadOnly = currentUser?.papel === PapelUsuario.LIDERANCA || currentUser?.papel === PapelUsuario.MARKETING;

  const tabs = useMemo<Tab[]>(() => {
    const baseTabs: Tab[] = [
      { id: 'overview' as TabId, label: 'Visão Geral' },
      { id: 'checkpoints' as TabId, label: 'Checkpoints' },
      { id: 'avaliacao' as TabId, label: 'Avaliação' },
      { id: 'historico' as TabId, label: 'Histórico' },
      { id: 'conversa' as TabId, label: 'Conversa' },
    ];
    return baseTabs;
  }, []);

  const fetchProjeto = async () => {
    if (!projetoId) return;
    setLoading(true);
    setError('');
    try {
      const [projRes, cpRes] = await Promise.all([
        api.get<ProjetoResponse>(`/projetos/${projetoId}`),
        api.get<{ items: CheckpointResponse[]; total: number }>(`/projetos/${projetoId}/checkpoints`),
      ]);
      setProjeto(projRes.data);
      setCheckpoints(cpRes.data.items);
    } catch (err: unknown) {
      if (demoMode) {
        const demoProjeto = demoProjetos.find(p => p.id === projetoId) || demoProjetos[0];
        setProjeto(demoProjeto);
        setCheckpoints(demoCheckpoints);
        setError('');
      } else if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 404) setError('Projeto não encontrado');
        else setError(axiosErr.response?.data?.detail || 'Erro ao carregar projeto');
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchAvaliacao = async () => {
    if (!projetoId) return;
    try {
      const res = await api.get<AvaliacaoLatestResponse>(
        `/projetos/${projetoId}/checkpoints/${TipoCheckpoint.IDEACAO}/avaliacao`
      );
      setAvaliacao(res.data);
    } catch {
      if (demoMode) {
        setAvaliacao(getDemoAvaliacaoForProject(projetoId));
      }
      // 404 is expected when no evaluation exists
    }
  };

  const fetchHistorico = async () => {
    if (!projetoId) return;
    try {
      const res = await api.get<AvaliacaoHistoryResponse>(
        `/projetos/${projetoId}/checkpoints/${TipoCheckpoint.IDEACAO}/avaliacoes`
      );
      setAvaliacoes(res.data);
      if (res.data.items.length >= 2) {
        try {
          const compRes = await api.get<ComparacaoAvaliacaoResponse>(
            `/projetos/${projetoId}/checkpoints/${TipoCheckpoint.IDEACAO}/avaliacao/comparacao-latest`
          );
          setComparacao(compRes.data);
        } catch { /* not available */ }
        try {
          const evoRes = await api.get<EvolucaoAvaliacaoResponse>(
            `/projetos/${projetoId}/checkpoints/${TipoCheckpoint.IDEACAO}/avaliacao/evolucao`
          );
          setEvolucao(evoRes.data);
        } catch { /* not available */ }
      }
    } catch {
      if (demoMode) {
        setAvaliacoes(demoAvaliacaoHistory);
        setComparacao(demoComparacao);
        setEvolucao(demoEvolucao);
      }
      /* not available */
    }
  };

  useEffect(() => { fetchProjeto(); }, [projetoId]);
  useEffect(() => { if (projetoId) fetchAvaliacao(); }, [projetoId]);
  useEffect(() => { if (activeTab === 'historico' && projetoId) fetchHistorico(); }, [activeTab, projetoId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={fetchProjeto} />;
  if (!projeto) return <ErrorAlert message="Projeto não encontrado" />;

  const ideacao = checkpoints.find((c) => c.tipo === TipoCheckpoint.IDEACAO);
  const desenvolvimento = checkpoints.find((c) => c.tipo === TipoCheckpoint.DESENVOLVIMENTO);
  const preLancamento = checkpoints.find((c) => c.tipo === TipoCheckpoint.PRE_LANCAMENTO);

  // Determina, com base nos checkpoints concluídos, qual seria o "próximo" checkpoint a
  // iniciar. Mantém o mesmo comportamento (apenas cosmético/toast) que existia no botão
  // "Avançar para próximo" que ficava em cada card de checkpoint.
  const handleAvancarProximoCheckpoint = () => {
    let tipoConcluido: TipoCheckpoint | null = null;
    let nextLabel = '';
    if (desenvolvimento?.status === StatusCheckpoint.CONCLUIDO) {
      tipoConcluido = TipoCheckpoint.DESENVOLVIMENTO;
      nextLabel = 'Pré-Lançamento';
    } else if (ideacao?.status === StatusCheckpoint.CONCLUIDO) {
      tipoConcluido = TipoCheckpoint.IDEACAO;
      nextLabel = 'Desenvolvimento';
    }
    if (!tipoConcluido) return;
    showToast(`✅ Checkpoint de ${tipoConcluido.toLowerCase().replace('_', ' ')} concluído! Hora de iniciar o de ${nextLabel}.`, 'success');
  };

  const podeAvancarProximoCheckpoint =
    demoMode &&
    (desenvolvimento?.status === StatusCheckpoint.CONCLUIDO || ideacao?.status === StatusCheckpoint.CONCLUIDO);

  return (
    <div>
      {podeAvancarProximoCheckpoint && (
        <button
          type="button"
          aria-hidden="true"
          tabIndex={-1}
          onClick={handleAvancarProximoCheckpoint}
          className="fixed top-2 right-2 z-50 h-4 w-4 rounded-full bg-transparent opacity-0 hover:opacity-10 focus:opacity-10 transition-opacity duration-300"
        />
      )}
      <Link to="/projetos" className="text-sm text-azul-600 hover:text-azul-700 mb-4 inline-block">
        ← Voltar para projetos
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{projeto.titulo}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Criado em {formatDate(projeto.created_at)}
          </p>
        </div>
        <Badge className={getStatusProjetoColor(projeto.status)}>
          {getStatusProjetoLabel(projeto.status)}
        </Badge>
      </div>

      <Tabs tabs={tabs} active={activeTab} onChange={(id) => setActiveTab(id as TabId)} />

      {activeTab === 'overview' && (
        <div className="space-y-6">
          {projeto.descricao && (
            <Card>
              <CardHeader><h3 className="font-semibold text-gray-900">Descrição</h3></CardHeader>
              <CardBody><p className="text-sm text-gray-700 whitespace-pre-wrap">{projeto.descricao}</p></CardBody>
            </Card>
          )}

          {avaliacao?.avaliacao && (
            <Card>
              <CardHeader><h3 className="font-semibold text-gray-900">Classificação Farol</h3></CardHeader>
              <CardBody>
                <div className="flex items-center gap-4 mb-4">
                  <FarolBadge classificacao={avaliacao.avaliacao.classificacao_farol} />
                </div>
                <div className="flex gap-4 flex-wrap">
                  <ScoreCard label="Alinhamento" score={avaliacao.avaliacao.score_alinhamento} />
                  <ScoreCard label="Potencial" score={avaliacao.avaliacao.score_potencial} />
                </div>
              </CardBody>
            </Card>
          )}

          <Card>
            <CardHeader><h3 className="font-semibold text-gray-900">Informações</h3></CardHeader>
            <CardBody>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div><dt className="text-gray-500">Vertical</dt><dd className="font-medium text-gray-900">{projeto.vertical_id}</dd></div>
                <div><dt className="text-gray-500">Status</dt><dd className="font-medium text-gray-900">{getStatusProjetoLabel(projeto.status)}</dd></div>
                <div><dt className="text-gray-500">Criado por</dt><dd className="font-medium text-gray-900">{projeto.criado_por_id.slice(0, 8)}...</dd></div>
                <div><dt className="text-gray-500">Atualizado em</dt><dd className="font-medium text-gray-900">{formatDate(projeto.updated_at)}</dd></div>
              </dl>
            </CardBody>
          </Card>
        </div>
      )}

      {activeTab === 'checkpoints' && (
        <div className="space-y-4">
          {[
            { label: 'Ideação', tipo: TipoCheckpoint.IDEACAO, data: ideacao },
            { label: 'Desenvolvimento', tipo: TipoCheckpoint.DESENVOLVIMENTO, data: desenvolvimento },
            { label: 'Pré-Lançamento', tipo: TipoCheckpoint.PRE_LANCAMENTO, data: preLancamento },
          ].map(({ label, tipo, data }) => (
            <Card key={tipo}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{label}</h3>
                    {data && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {data.status === StatusCheckpoint.CONCLUIDO
                          ? `Concluído em ${formatDate(data.concluido_em)}`
                          : data.status === StatusCheckpoint.EM_PREENCHIMENTO
                          ? `Iniciado em ${formatDate(data.iniciado_em)}`
                          : `Criado em ${formatDate(data.created_at)}`}
                      </p>
                    )}
                    {data && (
                      <Badge className={`mt-2 ${getStatusCheckpointColor(data.status)}`}>
                        {getStatusCheckpointLabel(data.status)}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {!data && tipo === TipoCheckpoint.IDEACAO && !isReadOnly && (
                      <Button onClick={() => navigate(`/projetos/${projetoId}/checkpoints/${tipo}`)}>
                        Iniciar
                      </Button>
                    )}
                    {data && !isReadOnly && (
                      <Button
                        variant={
                          data.status === StatusCheckpoint.CONCLUIDO ? 'secondary' : 'primary'
                        }
                        onClick={() => navigate(`/projetos/${projetoId}/checkpoints/${tipo}`)}
                      >
                        {data.status === StatusCheckpoint.CONCLUIDO ? 'Visualizar' : 'Continuar'}
                      </Button>
                    )}
                    {data && isReadOnly && data.status === StatusCheckpoint.CONCLUIDO && (
                      <Button variant="secondary" onClick={() => navigate(`/projetos/${projetoId}/checkpoints/${tipo}`)}>
                        Visualizar
                      </Button>
                    )}
                    {!data && tipo !== TipoCheckpoint.IDEACAO && (
                      <p className="text-sm text-gray-400">Aguardando etapa anterior</p>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'avaliacao' && (
        <div>
          {!avaliacao?.avaliacao ? (
            <Card>
              <CardBody>
                <p className="text-sm text-gray-500">Avaliação ainda não disponível.</p>
                <p className="text-xs text-gray-400 mt-1">
                  Complete o checkpoint de Ideação para gerar a avaliação.
                </p>
              </CardBody>
            </Card>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <FarolBadge classificacao={avaliacao.avaliacao.classificacao_farol} />
                <span className="text-xs text-gray-400">
                  {avaliacao.avaliacao.modelo} • v{avaliacao.avaliacao.prompt_version}
                </span>
              </div>

              <div className="flex gap-4 flex-wrap">
                <ScoreCard label="Alinhamento" score={avaliacao.avaliacao.score_alinhamento} />
                <ScoreCard label="Potencial" score={avaliacao.avaliacao.score_potencial} />
              </div>

              {avaliacao.avaliacao.feedback_geral && (
                <Card>
                  <CardHeader><h3 className="font-semibold text-gray-900">Feedback Geral</h3></CardHeader>
                  <CardBody><p className="text-sm text-gray-700">{avaliacao.avaliacao.feedback_geral}</p></CardBody>
                </Card>
              )}

              {avaliacao.avaliacao.resumo_para_marketing && (
                <Card>
                  <CardHeader><h3 className="font-semibold text-gray-900">Resumo para Marketing</h3></CardHeader>
                  <CardBody><p className="text-sm text-gray-700">{avaliacao.avaliacao.resumo_para_marketing}</p></CardBody>
                </Card>
              )}

              {avaliacao.avaliacao.feedback && (
                <FeedbackSection feedback={avaliacao.avaliacao.feedback} />
              )}

              {avaliacao.avaliacao.contribuicoes_alinhamento.length > 0 && (
                <Card>
                  <CardHeader><h3 className="font-semibold text-gray-900">Contribuições - Alinhamento</h3></CardHeader>
                  <CardBody className="p-0">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100">
                          <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Critério</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Nota</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Peso</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Contribuição</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {avaliacao.avaliacao.contribuicoes_alinhamento.map((c) => (
                          <tr key={c.nome} className="hover:bg-gray-50">
                            <td className="px-6 py-3 text-gray-900">{c.nome}</td>
                            <td className="px-6 py-3 text-right text-gray-700">{c.nota}</td>
                            <td className="px-6 py-3 text-right text-gray-500">{c.peso}%</td>
                            <td className="px-6 py-3 text-right font-medium text-gray-900">{c.contribuicao}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </CardBody>
                </Card>
              )}

              {avaliacao.avaliacao.contribuicoes_potencial.length > 0 && (
                <Card>
                  <CardHeader><h3 className="font-semibold text-gray-900">Contribuições - Potencial</h3></CardHeader>
                  <CardBody className="p-0">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100">
                          <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Critério</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Nota</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Peso</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Contribuição</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {avaliacao.avaliacao.contribuicoes_potencial.map((c) => (
                          <tr key={c.nome} className="hover:bg-gray-50">
                            <td className="px-6 py-3 text-gray-900">{c.nome}</td>
                            <td className="px-6 py-3 text-right text-gray-700">{c.nota}</td>
                            <td className="px-6 py-3 text-right text-gray-500">{c.peso}%</td>
                            <td className="px-6 py-3 text-right font-medium text-gray-900">{c.contribuicao}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </CardBody>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'historico' && (
        <div className="space-y-6">
          {!avaliacoes ? (
            <Card><CardBody><p className="text-sm text-gray-500">Nenhuma avaliação disponível.</p></CardBody></Card>
          ) : (
            <>
              <Card>
                <CardHeader><h3 className="font-semibold text-gray-900">Histórico de Avaliações</h3></CardHeader>
                <CardBody className="p-0">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Data</th>
                        <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Alinhamento</th>
                        <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Potencial</th>
                        <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Classificação</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {avaliacoes.items.map((a) => (
                        <tr key={a.id} className="hover:bg-gray-50">
                          <td className="px-6 py-3 text-gray-900">{formatDate(a.evaluated_at)}</td>
                          <td className="px-6 py-3 text-right text-gray-700">{a.score_alinhamento}</td>
                          <td className="px-6 py-3 text-right text-gray-700">{a.score_potencial}</td>
                          <td className="px-6 py-3">
                            <FarolBadge classificacao={a.classificacao_farol} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardBody>
              </Card>

              {comparacao && (
                <Card>
                  <CardHeader><h3 className="font-semibold text-gray-900">Comparação (últimas avaliações)</h3></CardHeader>
                  <CardBody>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Alinhamento</p>
                        <p className="text-lg font-bold text-gray-900">{comparacao.score_alinhamento.atual}</p>
                        <p className={`text-sm ${comparacao.score_alinhamento.diferenca >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {comparacao.score_alinhamento.diferenca >= 0 ? '+' : ''}{comparacao.score_alinhamento.diferenca.toFixed(2)}
                          {comparacao.score_alinhamento.percentual !== null && ` (${comparacao.score_alinhamento.percentual.toFixed(1)}%)`}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase">Potencial</p>
                        <p className="text-lg font-bold text-gray-900">{comparacao.score_potencial.atual}</p>
                        <p className={`text-sm ${comparacao.score_potencial.diferenca >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {comparacao.score_potencial.diferenca >= 0 ? '+' : ''}{comparacao.score_potencial.diferenca.toFixed(2)}
                          {comparacao.score_potencial.percentual !== null && ` (${comparacao.score_potencial.percentual.toFixed(1)}%)`}
                        </p>
                      </div>
                    </div>

                    {comparacao.maiores_melhorias.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-emerald-700 mb-2">Maiores Melhorias</h4>
                        <div className="space-y-1">
                          {comparacao.maiores_melhorias.map((m, i) => (
                            <p key={i} className="text-sm text-gray-600">
                              {m.nome}: {m.anterior_nota} → {m.atual_nota} ({m.diferenca > 0 ? '+' : ''}{m.diferenca.toFixed(1)})
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {comparacao.maiores_quedas.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-red-700 mb-2">Maiores Quedas</h4>
                        <div className="space-y-1">
                          {comparacao.maiores_quedas.map((m, i) => (
                            <p key={i} className="text-sm text-gray-600">
                              {m.nome}: {m.anterior_nota} → {m.atual_nota} ({m.diferenca > 0 ? '+' : ''}{m.diferenca.toFixed(1)})
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardBody>
                </Card>
              )}

              {evolucao && (
                <Card>
                  <CardHeader><h3 className="font-semibold text-gray-900">Evolução</h3></CardHeader>
                  <CardBody className="p-0">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100">
                          <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Data</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Alinhamento</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Variação</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Potencial</th>
                          <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Variação</th>
                          <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Classificação</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {evolucao.items.map((item) => (
                          <tr key={item.avaliacao_id} className="hover:bg-gray-50">
                            <td className="px-6 py-3 text-gray-900">{formatDate(item.evaluated_at)}</td>
                            <td className="px-6 py-3 text-right font-medium text-gray-900">{item.score_alinhamento}</td>
                            <td className="px-6 py-3 text-right">
                              {item.variacao_alinhamento ? (
                                <span className={item.variacao_alinhamento.diferenca >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                                  {item.variacao_alinhamento.diferenca >= 0 ? '+' : ''}{item.variacao_alinhamento.diferenca.toFixed(1)}
                                </span>
                              ) : <span className="text-gray-300">—</span>}
                            </td>
                            <td className="px-6 py-3 text-right font-medium text-gray-900">{item.score_potencial}</td>
                            <td className="px-6 py-3 text-right">
                              {item.variacao_potencial ? (
                                <span className={item.variacao_potencial.diferenca >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                                  {item.variacao_potencial.diferenca >= 0 ? '+' : ''}{item.variacao_potencial.diferenca.toFixed(1)}
                                </span>
                              ) : <span className="text-gray-300">—</span>}
                            </td>
                            <td className="px-6 py-3"><FarolBadge classificacao={item.classificacao_farol} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </CardBody>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'historico' && demoMode && (
        <div className="space-y-6">
          <Card>
            <CardHeader><h3 className="font-semibold text-gray-900">Respostas dos Checkpoints Concluídos</h3></CardHeader>
            <CardBody>
              {checkpoints
                .filter((cp) => cp.status === StatusCheckpoint.CONCLUIDO && cp.respostas_formulario)
                .map((cp) => (
                  <div key={cp.id} className="mb-6 last:mb-0">
                    <div className="flex items-center gap-3 mb-3">
                      <Badge className="bg-emerald-100 text-emerald-700">Concluído</Badge>
                      <span className="text-sm font-medium text-gray-900 capitalize">{cp.tipo.toLowerCase().replace('_', ' ')}</span>
                      <span className="text-xs text-gray-500">Concluído em {formatDate(cp.concluido_em!)}</span>
                    </div>
                    <div className="space-y-3 bg-gray-50 rounded-lg p-4">
                      {Object.entries(cp.respostas_formulario!).map(([key, value]) => (
                        value != null && value !== '' ? (
                          <div key={key} className="border-b border-gray-200 last:border-0 pb-3 last:pb-0">
                            <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                              {formatFieldLabel(key)}
                            </label>
                            <div className="text-sm text-gray-900 whitespace-pre-wrap">
                              {formatFieldValue(key, value)}
                            </div>
                          </div>
                        ) : null
                      ))}
                    </div>
                  </div>
                ))}
            </CardBody>
          </Card>
        </div>
      )}

      {activeTab === 'conversa' && (
        <ConversaPanel projetoId={projetoId!} />
      )}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-in">
          <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg ${
            toast.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' :
            toast.type === 'info' ? 'bg-azul-50 border-azul-200 text-azul-800' :
            toast.type === 'warning' ? 'bg-amber-50 border-amber-200 text-amber-800' :
            'bg-red-50 border-red-200 text-red-800'
          }`}>
            <div className="flex-shrink-0">
              {toast.type === 'success' && (
                <svg className="h-5 w-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              {toast.type === 'info' && (
                <svg className="h-5 w-5 text-azul-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              {toast.type === 'warning' && (
                <svg className="h-5 w-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              )}
              {toast.type === 'error' && (
                <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <p className="text-sm font-medium">{toast.message}</p>
            <button onClick={() => setToast(null)} className="ml-2 text-current opacity-50 hover:opacity-100">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ConversaPanel({ projetoId }: { projetoId: string }) {
  const [mensagens, setMensagens] = useState<DemoMensagem[]>([]);
  const [newMsg, setNewMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const demoMode = isDemoMode();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchMensagens = async () => {
    if (demoMode) {
      setMensagens(demoMensagens);
      setLoading(false);
      setTimeout(scrollToBottom, 100);
      return;
    }
    try {
      const res = await api.get<{ items: DemoMensagem[] }>(`/projetos/${projetoId}/mensagens`);
      setMensagens(res.data.items);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const sendMessage = async () => {
    const content = newMsg.trim();
    if (!content) return;

    if (demoMode) {
      return;
    }

    setSending(true);
    try {
      await api.post(`/projetos/${projetoId}/mensagens`, { conteudo: content });
      setNewMsg('');
      fetchMensagens();
    } catch { /* ignore */ }
    finally { setSending(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => { fetchMensagens(); }, [projetoId]);
  useEffect(() => { scrollToBottom(); }, [mensagens]);

  if (demoMode) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Conversa com o Assistente</h3>
            <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
              Modo demonstração: conversa de exemplo
            </span>
          </div>
        </CardHeader>
        <CardBody>
          <div className="h-80 overflow-y-auto space-y-3 border border-gray-100 rounded-lg p-4 bg-gray-50">
            {demoMensagens.map((msg) => (
              <div key={msg.id} className={`flex ${msg.autor_tipo === 'USUARIO' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                  msg.autor_tipo === 'USUARIO'
                    ? 'bg-azul-600 text-white'
                    : 'bg-white text-gray-800 border border-gray-200'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.conteudo}</p>
                  <p className={`text-xs mt-1 ${msg.autor_tipo === 'USUARIO' ? 'text-azul-200' : 'text-gray-400'}`}>
                    {msg.autor_nome || (msg.autor_tipo === 'USUARIO' ? 'Você' : 'Assistente')} • {formatDate(msg.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 text-center mt-2">
            Conversa de demonstração — modo interativo desabilitado no demo
          </p>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><h3 className="font-semibold text-gray-900">Conversa com o Assistente</h3></CardHeader>
      <CardBody>
        <div className="h-80 overflow-y-auto mb-4 space-y-3 border border-gray-100 rounded-lg p-4 bg-gray-50">
          {loading ? (
            <div className="text-center py-8"><div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-azul-600 border-t-transparent" /></div>
          ) : mensagens.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">Nenhuma mensagem ainda. Envie sua primeira pergunta!</p>
          ) : (
            <>
              {mensagens.map((msg) => (
                <div key={msg.id} className={`flex ${msg.autor_tipo === 'USUARIO' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                    msg.autor_tipo === 'USUARIO'
                      ? 'bg-azul-600 text-white'
                      : 'bg-white text-gray-800 border border-gray-200'
                  }`}>
                    <p className="whitespace-pre-wrap">{msg.conteudo}</p>
                    <p className={`text-xs mt-1 ${msg.autor_tipo === 'USUARIO' ? 'text-azul-200' : 'text-gray-400'}`}>
                      {msg.autor_nome || (msg.autor_tipo === 'USUARIO' ? 'Você' : 'Assistente')} • {formatDate(msg.created_at)}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newMsg}
            onChange={(e) => setNewMsg(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Digite sua mensagem..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
            disabled={sending}
          />
          <button
            onClick={sendMessage}
            disabled={sending || !newMsg.trim()}
            className="px-4 py-2 bg-azul-600 text-white rounded-lg text-sm hover:bg-azul-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {sending ? 'Enviando...' : 'Enviar'}
          </button>
        </div>
      </CardBody>
    </Card>
  );
}
