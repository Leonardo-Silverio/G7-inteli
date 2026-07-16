import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import { Card, CardBody, CardHeader } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { formatDate } from '../utils/formatters';
import {
  StatusCheckpoint,
  FocoAzul,
  ImpactoRotas,
  PrazoMercado,
  type CheckpointResponse,
} from '../types';
import { isDemoMode } from '../demo/demoData';

const FOCO_OPTIONS = Object.values(FocoAzul);
const IMPACTO_OPTIONS = Object.values(ImpactoRotas);
const PRAZO_OPTIONS = Object.values(PrazoMercado);

export function CheckpointForm() {
  const { projetoId, tipo } = useParams<{ projetoId: string; tipo: string }>();
  const [checkpoint, setCheckpoint] = useState<CheckpointResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [demoMsg, setDemoMsg] = useState('');

  const demoMode = isDemoMode();

  const [descricao_projeto, setDescricaoProjeto] = useState('');
  const [proposta_solucao, setPropostaSolucao] = useState('');
  const [focos_azul, setFocosAzul] = useState<string[]>([]);
  const [impacto_rotas, setImpactoRotas] = useState('');
  const [existe_semelhante, setExisteSemelhante] = useState(false);
  const [semelhante_descricao, setSemelhanteDescricao] = useState('');
  const [prazo_mercado, setPrazoMercado] = useState('');
  const [dependencia_critica, setDependenciaCritica] = useState(false);
  const [dependencia_descricao, setDependenciaDescricao] = useState('');
  const [diferencial, setDiferencial] = useState('');
  const [info_nao_compartilhada, setInfoNaoCompartilhada] = useState(false);
  const [info_nao_compartilhada_descricao, setInfoNaoCompartilhadaDescricao] = useState('');

  const isConcluido = checkpoint?.status === StatusCheckpoint.CONCLUIDO;

  const loadCheckpoint = async () => {
    if (!projetoId || !tipo) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get<CheckpointResponse>(
        `/projetos/${projetoId}/checkpoints/${tipo}`
      );
      setCheckpoint(res.data);
      const respostas = res.data.respostas_formulario as Record<string, unknown> | null;
      if (respostas) {
        setDescricaoProjeto((respostas.descricao_projeto as string) || '');
        setPropostaSolucao((respostas.proposta_solucao as string) || '');
        setFocosAzul((respostas.focos_azul as string[]) || []);
        setImpactoRotas((respostas.impacto_rotas as string) || '');
        setExisteSemelhante((respostas.existe_semelhante as boolean) || false);
        setSemelhanteDescricao((respostas.semelhante_descricao as string) || '');
        setPrazoMercado((respostas.prazo_mercado as string) || '');
        setDependenciaCritica((respostas.dependencia_critica as boolean) || false);
        setDependenciaDescricao((respostas.dependencia_descricao as string) || '');
        setDiferencial((respostas.diferencial as string) || '');
        setInfoNaoCompartilhada((respostas.info_nao_compartilhada as boolean) || false);
        setInfoNaoCompartilhadaDescricao((respostas.info_nao_compartilhada_descricao as string) || '');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
        if (axiosErr.response?.status === 404) {
          setCheckpoint(null);
        } else {
          setError(axiosErr.response?.data?.detail || 'Erro ao carregar checkpoint');
        }
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setLoading(false);
    }
  };

  const startCheckpoint = async () => {
    if (!projetoId || !tipo) return;
    if (demoMode) {
      setDemoMsg('Modo demonstração: esta ação não altera dados reais.');
      setTimeout(() => setDemoMsg(''), 3000);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.post<{ checkpoint: CheckpointResponse }>(
        `/projetos/${projetoId}/checkpoints/${tipo}/iniciar`
      );
      setCheckpoint(res.data.checkpoint);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 409) {
          setError(axiosErr.response?.data?.detail || 'Checkpoint já existe');
        } else {
          setError(axiosErr.response?.data?.detail || 'Erro ao iniciar checkpoint');
        }
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setLoading(false);
    }
  };

  const saveDraft = async () => {
    if (!projetoId || !tipo || !checkpoint) return;
    if (demoMode) {
      setDemoMsg('Modo demonstração: esta ação não altera dados reais.');
      setTimeout(() => setDemoMsg(''), 3000);
      return;
    }
    setSaving(true);
    setError('');
    try {
      await api.patch(`/projetos/${projetoId}/checkpoints/${tipo}/respostas`, {
        versao_formulario: 'ideacao_v1',
        versao_business: '2026-07',
        schema_version: 1,
        tipo_checkpoint: tipo,
        respostas: getFormData(),
      });
      setSuccessMsg('Rascunho salvo com sucesso!');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Erro ao salvar rascunho');
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setSaving(false);
    }
  };

  const submitCheckpoint = async () => {
    if (!projetoId || !tipo || !checkpoint) return;
    if (demoMode) {
      setDemoMsg('Modo demonstração: esta ação não altera dados reais.');
      setTimeout(() => setDemoMsg(''), 3000);
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/projetos/${projetoId}/checkpoints/${tipo}/enviar`, {
        versao_formulario: 'ideacao_v1',
        versao_business: '2026-07',
        schema_version: 1,
        tipo_checkpoint: tipo,
        respostas: getFormData(),
      });
      setSuccessMsg('Checkpoint enviado com sucesso! A avaliação está sendo processada.');
      loadCheckpoint();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 409) {
          setError(axiosErr.response?.data?.detail || 'Ordem de checkpoints não respeitada');
        } else {
          setError(axiosErr.response?.data?.detail || 'Erro ao enviar checkpoint');
        }
      } else {
        setError('Erro de conexão');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getFormData = () => ({
    descricao_projeto,
    proposta_solucao,
    focos_azul,
    impacto_rotas,
    existe_semelhante,
    semelhante_descricao: existe_semelhante ? semelhante_descricao : null,
    prazo_mercado,
    dependencia_critica,
    dependencia_descricao: dependencia_critica ? dependencia_descricao : null,
    diferencial,
    info_nao_compartilhada,
    info_nao_compartilhada_descricao: info_nao_compartilhada ? info_nao_compartilhada_descricao : null,
  });

  const toggleFoco = (foco: string) => {
    if (foco === FocoAzul.NENHUM) {
      setFocosAzul([FocoAzul.NENHUM]);
    } else {
      setFocosAzul((prev) => {
        const next = prev.filter((f) => f !== FocoAzul.NENHUM);
        return next.includes(foco) ? next.filter((f) => f !== foco) : [...next, foco];
      });
    }
  };

  useEffect(() => { loadCheckpoint(); }, [projetoId, tipo]);

  if (loading) return <LoadingSpinner />;

  if (!checkpoint) {
    return (
      <div className="max-w-2xl mx-auto">
        <Link to={`/projetos/${projetoId}`} className="text-sm text-azul-600 hover:text-azul-700 mb-4 inline-block">
          ← Voltar
        </Link>
        <Card>
          <CardBody className="text-center py-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Checkpoint não iniciado</h2>
            <p className="text-sm text-gray-500 mb-4">Clique abaixo para iniciar o checkpoint de {tipo}.</p>
            {!demoMode && <Button onClick={startCheckpoint}>Iniciar Checkpoint</Button>}
            {demoMode && (
              <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
                Modo demonstração: ações de escrita desabilitadas.
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    );
  }

  if (isConcluido) {
    return (
      <div className="max-w-2xl mx-auto">
        <Link to={`/projetos/${projetoId}`} className="text-sm text-azul-600 hover:text-azul-700 mb-4 inline-block">
          ← Voltar para o projeto
        </Link>
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Checkpoint {tipo} — Concluído</h3></CardHeader>
          <CardBody>
            <p className="text-sm text-gray-500 mb-4">
              Este checkpoint foi concluído em {formatDate(checkpoint.concluido_em)}.
            </p>
            <div className="bg-gray-50 rounded-lg p-4">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                {JSON.stringify(checkpoint.respostas_formulario, null, 2)}
              </pre>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <Link to={`/projetos/${projetoId}`} className="text-sm text-azul-600 hover:text-azul-700 mb-4 inline-block">
        ← Voltar para o projeto
      </Link>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Checkpoint de {tipo}</h2>
            {checkpoint.iniciado_em && (
              <span className="text-xs text-gray-400">Iniciado em {formatDate(checkpoint.iniciado_em)}</span>
            )}
          </div>
        </CardHeader>
        <CardBody>
          {error && <div className="mb-4"><ErrorAlert message={error} /></div>}
          {successMsg && (
            <div className="mb-4 bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-700">
              {successMsg}
            </div>
          )}
          {demoMsg && (
            <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700">
              {demoMsg}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descrição do Projeto <span className="text-red-500">*</span>
              </label>
              <textarea
                value={descricao_projeto}
                onChange={(e) => setDescricaoProjeto(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                rows={3}
                maxLength={500}
                placeholder="Descreva o projeto em até 500 caracteres"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Proposta da Solução <span className="text-red-500">*</span>
              </label>
              <textarea
                value={proposta_solucao}
                onChange={(e) => setPropostaSolucao(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                rows={3}
                maxLength={500}
                placeholder="Qual é a proposta da solução?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Focos da Azul <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {FOCO_OPTIONS.map((foco) => (
                  <button
                    key={foco}
                    type="button"
                    onClick={() => toggleFoco(foco)}
                    className={`px-3 py-2 text-sm rounded-lg border text-left transition-colors ${
                      focos_azul.includes(foco)
                        ? 'bg-azul-50 border-azul-300 text-azul-700'
                        : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {foco === FocoAzul.RECONQUISTA_CLIENTE ? 'Reconquista de Cliente' :
                     foco === FocoAzul.FORTALECIMENTO_MALHA_REGIONAL ? 'Fortalecimento Malha Regional' :
                     foco === FocoAzul.DIVERSIFICACAO_RECEITA ? 'Diversificação de Receita' :
                     foco === FocoAzul.DISCIPLINA_FINANCEIRA ? 'Disciplina Financeira' :
                     foco}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Impacto em Rotas <span className="text-red-500">*</span>
              </label>
              <select
                value={impacto_rotas}
                onChange={(e) => setImpactoRotas(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
              >
                <option value="">Selecione...</option>
                {IMPACTO_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt === ImpactoRotas.ROTAS_REGIONAIS ? 'Rotas Regionais' :
                     opt === ImpactoRotas.ROTAS_PRINCIPAIS_COMPETITIVAS ? 'Rotas Principais Competitivas' :
                     opt === ImpactoRotas.AMBAS ? 'Ambas' :
                     'Não é sobre rotas'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Projeto Semelhante
              </label>
              <div className="flex items-center gap-3 mb-2">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={existe_semelhante}
                    onChange={(e) => setExisteSemelhante(e.target.checked)}
                    className="rounded border-gray-300 text-azul-600 focus:ring-azul-500"
                  />
                  Existe projeto semelhante
                </label>
              </div>
              {existe_semelhante && (
                <textarea
                  value={semelhante_descricao}
                  onChange={(e) => setSemelhanteDescricao(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                  rows={2}
                  maxLength={300}
                  placeholder="Descreva o projeto semelhante"
                />
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prazo Estimado <span className="text-red-500">*</span>
              </label>
              <select
                value={prazo_mercado}
                onChange={(e) => setPrazoMercado(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
              >
                <option value="">Selecione...</option>
                {PRAZO_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt === PrazoMercado.ATE_1_MES ? 'Até 1 mês' :
                     opt === PrazoMercado.DE_1_A_3_MESES ? '1 a 3 meses' :
                     opt === PrazoMercado.DE_3_A_6_MESES ? '3 a 6 meses' :
                     'Mais de 6 meses'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dependência Crítica
              </label>
              <div className="flex items-center gap-3 mb-2">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dependencia_critica}
                    onChange={(e) => setDependenciaCritica(e.target.checked)}
                    className="rounded border-gray-300 text-azul-600 focus:ring-azul-500"
                  />
                  Existe dependência crítica
                </label>
              </div>
              {dependencia_critica && (
                <textarea
                  value={dependencia_descricao}
                  onChange={(e) => setDependenciaDescricao(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                  rows={2}
                  maxLength={300}
                  placeholder="Descreva a dependência crítica"
                />
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Diferenciação <span className="text-red-500">*</span>
              </label>
              <textarea
                value={diferencial}
                onChange={(e) => setDiferencial(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                rows={4}
                maxLength={1000}
                placeholder="O que diferencia este projeto?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Informação Não Compartilhada
              </label>
              <div className="flex items-center gap-3 mb-2">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={info_nao_compartilhada}
                    onChange={(e) => setInfoNaoCompartilhada(e.target.checked)}
                    className="rounded border-gray-300 text-azul-600 focus:ring-azul-500"
                  />
                  Há informação não compartilhada
                </label>
              </div>
              {info_nao_compartilhada && (
                <textarea
                  value={info_nao_compartilhada_descricao}
                  onChange={(e) => setInfoNaoCompartilhadaDescricao(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                  rows={2}
                  maxLength={300}
                  placeholder="Descreva a informação"
                />
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 pt-6 border-t border-gray-100 mt-6">
            {!demoMode && (
              <>
                <Button onClick={saveDraft} loading={saving} variant="secondary">
                  Salvar Rascunho
                </Button>
                <Button onClick={submitCheckpoint} loading={submitting}>
                  Enviar Checkpoint
                </Button>
              </>
            )}
            {demoMode && (
              <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
                Modo demonstração: ações de escrita desabilitadas.
              </div>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
