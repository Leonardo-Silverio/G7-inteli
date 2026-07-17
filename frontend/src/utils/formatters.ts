import { ClassificacaoFarol, StatusProjeto, StatusCheckpoint } from '../types';

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDateShort(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function getFarolLabel(classificacao?: ClassificacaoFarol | null): string {
  if (!classificacao) return '⚪ Sem Avaliação';
  const labels: Record<ClassificacaoFarol, string> = {
    [ClassificacaoFarol.PRIORIDADE_MAXIMA]: '🔴 Prioridade Máxima',
    [ClassificacaoFarol.VALE_INVESTIR_TEMPO]: '🟡 Vale Investir Tempo',
    [ClassificacaoFarol.BAIXA_PRIORIDADE]: '🟢 Baixa Prioridade',
  };
  return labels[classificacao] || classificacao;
}

export function getFarolColor(classificacao?: ClassificacaoFarol | null): string {
  if (!classificacao) return 'text-slate-600 bg-slate-100 border-slate-200';
  const colors: Record<ClassificacaoFarol, string> = {
    [ClassificacaoFarol.PRIORIDADE_MAXIMA]: 'text-red-700 bg-red-100 border-red-200',
    [ClassificacaoFarol.VALE_INVESTIR_TEMPO]: 'text-amber-700 bg-amber-100 border-amber-200',
    [ClassificacaoFarol.BAIXA_PRIORIDADE]: 'text-green-700 bg-green-100 border-green-200',
  };
  return colors[classificacao] || 'text-slate-600 bg-slate-100 border-slate-200';
}

export function getStatusProjetoLabel(status: StatusProjeto): string {
  const labels: Record<StatusProjeto, string> = {
    [StatusProjeto.EM_IDEACAO]: 'Em Ideação',
    [StatusProjeto.EM_DESENVOLVIMENTO]: 'Em Desenvolvimento',
    [StatusProjeto.AGUARDANDO_PRE_LANCAMENTO]: 'Aguardando Pré-Lançamento',
    [StatusProjeto.APROVADO_PARA_LANCAMENTO]: 'Aprovado para Lançamento',
    [StatusProjeto.LANCADO]: 'Lançado',
    [StatusProjeto.EM_ALERTA]: 'Em Alerta',
    [StatusProjeto.ENCERRADO]: 'Encerrado',
  };
  return labels[status] || status;
}

export function getStatusProjetoColor(status: StatusProjeto): string {
  const colors: Record<StatusProjeto, string> = {
    [StatusProjeto.EM_IDEACAO]: 'bg-blue-100 text-blue-700',
    [StatusProjeto.EM_DESENVOLVIMENTO]: 'bg-indigo-100 text-indigo-700',
    [StatusProjeto.AGUARDANDO_PRE_LANCAMENTO]: 'bg-purple-100 text-purple-700',
    [StatusProjeto.APROVADO_PARA_LANCAMENTO]: 'bg-emerald-100 text-emerald-700',
    [StatusProjeto.LANCADO]: 'bg-green-100 text-green-700',
    [StatusProjeto.EM_ALERTA]: 'bg-red-100 text-red-700',
    [StatusProjeto.ENCERRADO]: 'bg-gray-100 text-gray-700',
  };
  return colors[status] || 'bg-gray-100 text-gray-700';
}

export function getStatusCheckpointLabel(status: StatusCheckpoint): string {
  const labels: Record<StatusCheckpoint, string> = {
    [StatusCheckpoint.PENDENTE]: 'Pendente',
    [StatusCheckpoint.SUGERIDO]: 'Sugerido',
    [StatusCheckpoint.EM_PREENCHIMENTO]: 'Em Preenchimento',
    [StatusCheckpoint.CONCLUIDO]: 'Concluído',
  };
  return labels[status] || status;
}

export function getStatusCheckpointColor(status: StatusCheckpoint): string {
  const colors: Record<StatusCheckpoint, string> = {
    [StatusCheckpoint.PENDENTE]: 'bg-gray-100 text-gray-600',
    [StatusCheckpoint.SUGERIDO]: 'bg-yellow-100 text-yellow-700',
    [StatusCheckpoint.EM_PREENCHIMENTO]: 'bg-blue-100 text-blue-700',
    [StatusCheckpoint.CONCLUIDO]: 'bg-emerald-100 text-emerald-700',
  };
  return colors[status] || 'bg-gray-100 text-gray-600';
}

export function formatFieldLabel(key: string): string {
  const labels: Record<string, string> = {
    descricao_projeto: 'Descrição do Projeto',
    proposta_solucao: 'Proposta da Solução',
    focos_azul: 'Focos da Azul',
    impacto_rotas: 'Impacto nas Rotas',
    existe_semelhante: 'Existe Projeto Semelhante',
    semelhante_descricao: 'Descrição do Projeto Semelhante',
    prazo_mercado: 'Prazo Estimado para Mercado',
    dependencias_criticas: 'Dependências Críticas',
    diferencial_concorrentes: 'Diferencial dos Concorrentes',
    info_adicional: 'Informações Adicionais',
    material_desenvolvido: 'Material Desenvolvido',
    produtos_marcas: 'Produtos/Marcas da Azul Envolvidos',
    tom_comunicacao: 'Tom de Comunicação (1-5)',
    mudancas_checkpoint1: 'Mudanças desde o Checkpoint 1',
    feedback_enderecado: 'Feedback do Checkpoint 1 Endereçado',
    limitacoes_internas: 'Limitações/Decisões Internas',
    material_final: 'Material Final (ou Quase Final)',
    areas_envolvidas_acordo: 'Áreas Envolvidas de Acordo',
    dados_clientes: 'Coleta/Uso de Dados de Clientes',
    revisao_juridica: 'Revisão Jurídica/Compliance',
    tarifas_confirmadas: 'Tarifas/Benefícios Confirmados',
    risco_interpretacao: 'Risco de Má Interpretação',
    conflito_mensagem: 'Conflito com Campanhas em Andamento',
    data_lancamento: 'Data Prevista de Lançamento',
    riscos_incertos: 'Riscos/Incertezas Antes do Lançamento',
  };
  return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export function formatFieldValue(_key: string, value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (Array.isArray(value)) {
    if (value.length === 0) return '—';
    return value.map((v) => String(v)).join(', ');
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}
