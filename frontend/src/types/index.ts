export enum PapelUsuario {
  VERTICAL = 'VERTICAL',
  MARKETING = 'MARKETING',
  LIDERANCA = 'LIDERANCA',
  ADMIN = 'ADMIN',
}

export enum StatusProjeto {
  EM_IDEACAO = 'EM_IDEACAO',
  EM_DESENVOLVIMENTO = 'EM_DESENVOLVIMENTO',
  AGUARDANDO_PRE_LANCAMENTO = 'AGUARDANDO_PRE_LANCAMENTO',
  APROVADO_PARA_LANCAMENTO = 'APROVADO_PARA_LANCAMENTO',
  LANCADO = 'LANCADO',
  EM_ALERTA = 'EM_ALERTA',
  ENCERRADO = 'ENCERRADO',
}

export enum TipoCheckpoint {
  IDEACAO = 'IDEACAO',
  DESENVOLVIMENTO = 'DESENVOLVIMENTO',
  PRE_LANCAMENTO = 'PRE_LANCAMENTO',
}

export enum StatusCheckpoint {
  PENDENTE = 'PENDENTE',
  SUGERIDO = 'SUGERIDO',
  EM_PREENCHIMENTO = 'EM_PREENCHIMENTO',
  CONCLUIDO = 'CONCLUIDO',
}

export enum ClassificacaoFarol {
  PRIORIDADE_MAXIMA = 'PRIORIDADE_MAXIMA',
  VALE_INVESTIR_TEMPO = 'VALE_INVESTIR_TEMPO',
  BAIXA_PRIORIDADE = 'BAIXA_PRIORIDADE',
}

export enum AutorMensagem {
  USUARIO = 'USUARIO',
  AGENTE = 'AGENTE',
  SISTEMA = 'SISTEMA',
}

export enum FocoAzul {
  RECONQUISTA_CLIENTE = 'RECONQUISTA_CLIENTE',
  FORTALECIMENTO_MALHA_REGIONAL = 'FORTALECIMENTO_MALHA_REGIONAL',
  DIVERSIFICACAO_RECEITA = 'DIVERSIFICACAO_RECEITA',
  DISCIPLINA_FINANCEIRA = 'DISCIPLINA_FINANCEIRA',
  NENHUM = 'NENHUM',
}

export enum ImpactoRotas {
  ROTAS_REGIONAIS = 'ROTAS_REGIONAIS',
  ROTAS_PRINCIPAIS_COMPETITIVAS = 'ROTAS_PRINCIPAIS_COMPETITIVAS',
  AMBAS = 'AMBAS',
  NAO_E_SOBRE_ROTAS = 'NAO_E_SOBRE_ROTAS',
}

export enum PrazoMercado {
  ATE_1_MES = 'ATE_1_MES',
  DE_1_A_3_MESES = '1_3_MESES',
  DE_3_A_6_MESES = '3_6_MESES',
  MAIS_DE_6_MESES = 'MAIS_6_MESES',
}

export interface CurrentUser {
  id: string;
  email: string;
  papel: PapelUsuario;
  vertical_id: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface ProjetoResponse {
  id: string;
  titulo: string;
  descricao: string | null;
  objetivo: string | null;
  vertical_id: string;
  criado_por_id: string;
  status: StatusProjeto;
  created_at: string;
  updated_at: string;
}

export interface ProjetoListResponse {
  items: ProjetoResponse[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface CheckpointResponse {
  id: string;
  projeto_id: string;
  tipo: TipoCheckpoint;
  status: StatusCheckpoint;
  sugerido_em: string | null;
  iniciado_em: string | null;
  concluido_em: string | null;
  respostas_formulario: Record<string, unknown> | null;
  resumo_para_marketing: string | null;
  created_at: string;
  updated_at: string;
}

export interface CheckpointListResponse {
  items: CheckpointResponse[];
  total: number;
}

export interface CheckpointStartResponse {
  checkpoint: CheckpointResponse;
  criado: boolean;
}

export interface CheckpointDraftResponse {
  checkpoint: CheckpointResponse;
  salvo_em: string;
}

export interface CheckpointSubmitResponse {
  checkpoint: CheckpointResponse;
  enviado_em: string;
  proxima_etapa: string | null;
}

export interface FeedbackItem {
  titulo: string;
  descricao: string;
  evidencias: string[];
  prioridade: 'ALTA' | 'MEDIA' | 'BAIXA' | null;
}

export interface FeedbackEstruturado {
  schema_version: string;
  justificativa_classificacao: string;
  pontos_fortes: FeedbackItem[];
  oportunidades_melhoria: FeedbackItem[];
  recomendacoes_praticas: FeedbackItem[];
  proximos_passos: string[];
  riscos_principais: FeedbackItem[];
}

export interface CriterioAvaliacao {
  nota: number;
  feedback: string;
  evidencias: string[];
  sugestoes: string[];
  confianca: number | null;
}

export interface CriteriosAlinhamento {
  tom_de_voz_azul: CriterioAvaliacao;
  identidade_visual_azul: CriterioAvaliacao;
  posicionamento_malha_regional: CriterioAvaliacao;
  uso_correto_produtos_marca: CriterioAvaliacao;
  seguranca_solidez: CriterioAvaliacao;
  clareza_passageiro: CriterioAvaliacao;
}

export interface CriteriosPotencial {
  pilares_estrategicos_atuais: CriterioAvaliacao;
  receita_produtos_proprios: CriterioAvaliacao;
  alcance_malha_regional: CriterioAvaliacao;
  diferenciacao_gol_latam: CriterioAvaliacao;
  recuperacao_fidelizacao_cliente: CriterioAvaliacao;
  viabilidade_operacional: CriterioAvaliacao;
}

export interface ContribuicaoCriterio {
  nome: string;
  nota: number;
  peso: number;
  contribuicao: number;
}

export interface AvaliacaoCheckpointResponse {
  id: string;
  checkpoint_id: string;
  score_alinhamento: number;
  score_potencial: number;
  classificacao_farol: ClassificacaoFarol;
  criterios_alinhamento: CriteriosAlinhamento;
  criterios_potencial: CriteriosPotencial;
  feedback_geral: string;
  resumo_para_marketing: string;
  evaluation_engine: string;
  modelo: string;
  prompt_version: string;
  criteria_version: string;
  evaluated_at: string;
  prompt_hash: string;
  criteria_hash: string;
  created_at: string;
  contribuicoes_alinhamento: ContribuicaoCriterio[];
  contribuicoes_potencial: ContribuicaoCriterio[];
  feedback: FeedbackEstruturado | null;
}

export interface AvaliacaoLatestResponse {
  avaliacao: AvaliacaoCheckpointResponse | null;
  total_historico: number;
}

export interface AvaliacaoHistoryResponse {
  items: AvaliacaoCheckpointResponse[];
  total: number;
}

export interface ConversaResponse {
  id: string;
  projeto_id: string;
  created_at: string;
  updated_at: string;
}

export interface MensagemResponse {
  id: string;
  conversa_id: string;
  autor_tipo: AutorMensagem;
  usuario_id: string | null;
  conteudo: string;
  created_at: string;
}

export interface MensagemListResponse {
  items: MensagemResponse[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface APIError {
  detail: string;
}

export interface VariacaoScore {
  anterior: number;
  atual: number;
  diferenca: number;
  percentual: number | null;
  estavel: boolean;
}

export interface VariacaoCriterio {
  nome: string;
  peso: number;
  anterior_nota: number;
  atual_nota: number;
  diferenca: number;
  percentual: number | null;
  estavel: boolean;
}

export interface ComparacaoAvaliacaoResponse {
  avaliacao_anterior_id: string;
  avaliacao_atual_id: string;
  checkpoint_id: string;
  score_alinhamento: VariacaoScore;
  score_potencial: VariacaoScore;
  criterios_alinhamento: VariacaoCriterio[];
  criterios_potencial: VariacaoCriterio[];
  maiores_melhorias: VariacaoCriterio[];
  maiores_quedas: VariacaoCriterio[];
}

export interface EvolucaoAvaliacaoItem {
  avaliacao_id: string;
  evaluated_at: string;
  score_alinhamento: number;
  score_potencial: number;
  classificacao_farol: ClassificacaoFarol;
  variacao_alinhamento: VariacaoScore | null;
  variacao_potencial: VariacaoScore | null;
}

export interface EvolucaoAvaliacaoResponse {
  checkpoint_id: string;
  items: EvolucaoAvaliacaoItem[];
  total: number;
}
