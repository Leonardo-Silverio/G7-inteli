from uuid import UUID
from datetime import datetime, date
from enum import StrEnum, IntEnum
from typing import Literal
from typing_extensions import Annotated

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.enums import TipoCheckpoint, StatusCheckpoint


class FocoAzul(StrEnum):
    RECONQUISTA_CLIENTE = "RECONQUISTA_CLIENTE"
    FORTALECIMENTO_MALHA_REGIONAL = "FORTALECIMENTO_MALHA_REGIONAL"
    DIVERSIFICACAO_RECEITA = "DIVERSIFICACAO_RECEITA"
    DISCIPLINA_FINANCEIRA = "DISCIPLINA_FINANCEIRA"
    NENHUM = "NENHUM"


class ImpactoRotas(StrEnum):
    ROTAS_REGIONAIS = "ROTAS_REGIONAIS"
    ROTAS_PRINCIPAIS_COMPETITIVAS = "ROTAS_PRINCIPAIS_COMPETITIVAS"
    AMBAS = "AMBAS"
    NAO_E_SOBRE_ROTAS = "NAO_E_SOBRE_ROTAS"


class PrazoMercado(StrEnum):
    ATE_1_MES = "ATE_1_MES"
    DE_1_A_3_MESES = "1_3_MESES"
    DE_3_A_6_MESES = "3_6_MESES"
    MAIS_DE_6_MESES = "MAIS_6_MESES"


class ProdutoAzul(StrEnum):
    AZUL_FIDELIDADE = "AZUL_FIDELIDADE"
    AZUL_VIAGENS = "AZUL_VIAGENS"
    AZUL_CARGO = "AZUL_CARGO"
    AZUL_EMPRESAS = "AZUL_EMPRESAS"
    NENHUM = "NENHUM"


class TomEscala(IntEnum):
    MUITO_PROXIMO = 1
    PROXIMO = 2
    NEUTRO = 3
    FORMAL = 4
    MUITO_FORMAL = 5


class AreasAcordo(StrEnum):
    SIM = "SIM"
    PARCIALMENTE = "PARCIALMENTE"
    NAO = "NAO"


class RevisaoJuridica(StrEnum):
    SIM = "SIM"
    NAO = "NAO"


class ComparadoCampanhas(StrEnum):
    SIM = "SIM"
    NAO = "NAO"


class StatusFeedbackCheckpoint(StrEnum):
    SIM = "SIM"
    PARCIALMENTE = "PARCIALMENTE"
    NAO = "NAO"


class StatusLimitacoesInternas(StrEnum):
    SIM = "SIM"
    PARCIALMENTE = "PARCIALMENTE"
    NAO = "NAO"


class AnexoReferencia(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    storage_key: str | None = None


class IdeacaoFormData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descricao_projeto: str = Field(min_length=10, max_length=500)
    proposta_solucao: str = Field(min_length=10, max_length=500)
    focos_azul: list[FocoAzul] = Field(min_length=1)
    impacto_rotas: ImpactoRotas
    existe_semelhante: bool
    semelhante_descricao: str | None = Field(default=None, max_length=300)
    prazo_mercado: PrazoMercado
    dependencia_critica: bool
    dependencia_descricao: str | None = Field(default=None, max_length=300)
    diferencial: str = Field(min_length=10, max_length=1000)
    info_nao_compartilhada: bool
    info_nao_compartilhada_descricao: str | None = Field(default=None, max_length=300)

    @field_validator("semelhante_descricao")
    @classmethod
    def validar_semelhante(cls, v, info):
        if info.data.get("existe_semelhante") and not v:
            raise ValueError("Descrição obrigatória quando existe projeto semelhante")
        return v

    @field_validator("dependencia_descricao")
    @classmethod
    def validar_dependencia(cls, v, info):
        if info.data.get("dependencia_critica") and not v:
            raise ValueError("Descrição obrigatória quando existe dependência crítica")
        return v

    @field_validator("info_nao_compartilhada_descricao")
    @classmethod
    def validar_info_nao_compartilhada(cls, v, info):
        if info.data.get("info_nao_compartilhada") and not v:
            raise ValueError("Descrição obrigatória quando há informação não compartilhada")
        return v

    @field_validator("focos_azul")
    @classmethod
    def validar_focos(cls, v):
        if "NENHUM" in v and len(v) > 1:
            raise ValueError("NENHUM não pode coexistir com outros focos")
        return v

    @field_validator("focos_azul")
    @classmethod
    def validar_duplicados(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Focos não podem conter duplicados")
        return v


class DesenvolvimentoFormData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_desenvolvido: str = Field(min_length=10, max_length=2000)
    produtos_azul: list[ProdutoAzul] = Field(min_length=1)
    tom_escala: TomEscala
    mudancas_desde_ideacao: str = Field(min_length=10, max_length=2000)
    feedback_ideacao_enderecado: StatusFeedbackCheckpoint
    feedback_explicacao: str | None = Field(default=None, max_length=1000)
    limitacoes_internas: StatusLimitacoesInternas
    limitacoes_explicacao: str | None = Field(default=None, max_length=1000)

    @field_validator("feedback_explicacao")
    @classmethod
    def validar_feedback(cls, v, info):
        val = info.data.get("feedback_ideacao_enderecado")
        if val in ("PARCIALMENTE", "NAO") and not v:
            raise ValueError("Explicação obrigatória quando feedback não foi totalmente endereçado")
        return v

    @field_validator("limitacoes_explicacao")
    @classmethod
    def validar_limitacoes(cls, v, info):
        if info.data.get("limitacoes_internas") == "SIM" and not v:
            raise ValueError("Explicação obrigatória quando existem limitações internas")
        return v

    @field_validator("produtos_azul")
    @classmethod
    def validar_produtos(cls, v):
        if "NENHUM" in v and len(v) > 1:
            raise ValueError("NENHUM não pode coexistir com outros produtos")
        if len(v) != len(set(v)):
            raise ValueError("Produtos não podem conter duplicados")
        return v


class PreLancamentoFormData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_final_descricao: str = Field(min_length=10, max_length=1000)
    areas_acordo: AreasAcordo
    areas_lista: str | None = Field(default=None, max_length=1000)
    dados_clientes: bool
    dados_clientes_descricao: str | None = Field(default=None, max_length=1000)
    revisao_juridica: RevisaoJuridica
    revisao_juridica_referencia: str | None = Field(default=None, max_length=500)
    tarifas_confirmadas: bool
    risco_interpretacao: bool
    risco_interpretacao_descricao: str | None = Field(default=None, max_length=500)
    comparado_campanhas: ComparadoCampanhas
    data_prevista_lancamento: date
    riscos_incertos: str = Field(min_length=1, max_length=500)

    @field_validator("areas_lista")
    @classmethod
    def validar_areas(cls, v, info):
        if info.data.get("areas_acordo") in ("PARCIALMENTE", "NAO") and not v:
            raise ValueError("Lista de áreas obrigatória quando não há acordo total")
        return v

    @field_validator("dados_clientes_descricao")
    @classmethod
    def validar_dados_clientes(cls, v, info):
        if info.data.get("dados_clientes") and not v:
            raise ValueError("Descrição obrigatória quando envolve dados de clientes")
        return v

    @field_validator("risco_interpretacao_descricao")
    @classmethod
    def validar_risco(cls, v, info):
        if info.data.get("risco_interpretacao") and not v:
            raise ValueError("Descrição obrigatória quando há risco de má interpretação")
        return v


class CheckpointFormularioBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_formulario: Literal["ideacao_v1", "desenvolvimento_v1", "pre_lancamento_v1"]
    versao_business: Literal["2026-07"]
    schema_version: Literal[1]
    tipo_checkpoint: TipoCheckpoint
    respostas: IdeacaoFormData | DesenvolvimentoFormData | PreLancamentoFormData
    anexos: list[AnexoReferencia] = Field(default_factory=list)
    enviado_em: datetime | None = None
    atualizado_em: datetime | None = None


class CheckpointIniciarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CheckpointSalvarRespostasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_formulario: Literal["ideacao_v1", "desenvolvimento_v1", "pre_lancamento_v1"]
    versao_business: Literal["2026-07"]
    schema_version: Literal[1]
    tipo_checkpoint: TipoCheckpoint
    respostas: dict
    anexos: list[AnexoReferencia] = Field(default_factory=list)


class CheckpointEnviarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_formulario: Literal["ideacao_v1", "desenvolvimento_v1", "pre_lancamento_v1"]
    versao_business: Literal["2026-07"]
    schema_version: Literal[1]
    tipo_checkpoint: TipoCheckpoint
    respostas: dict


class IdeacaoFormEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_formulario: Literal["ideacao_v1"]
    versao_business: Literal["2026-07"]
    schema_version: Literal[1]
    tipo_checkpoint: TipoCheckpoint = TipoCheckpoint.IDEACAO
    respostas: IdeacaoFormData
    anexos: list[AnexoReferencia] = Field(default_factory=list)
    enviado_em: datetime | None = None
    atualizado_em: datetime | None = None


class DesenvolvimentoFormEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_formulario: Literal["desenvolvimento_v1"]
    versao_business: Literal["2026-07"]
    schema_version: Literal[1]
    tipo_checkpoint: TipoCheckpoint = TipoCheckpoint.DESENVOLVIMENTO
    respostas: DesenvolvimentoFormData
    anexos: list[AnexoReferencia] = Field(default_factory=list)
    enviado_em: datetime | None = None
    atualizado_em: datetime | None = None


class PreLancamentoFormEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_formulario: Literal["pre_lancamento_v1"]
    versao_business: Literal["2026-07"]
    schema_version: Literal[1]
    tipo_checkpoint: TipoCheckpoint = TipoCheckpoint.PRE_LANCAMENTO
    respostas: PreLancamentoFormData
    anexos: list[AnexoReferencia] = Field(default_factory=list)
    enviado_em: datetime | None = None
    atualizado_em: datetime | None = None


class AnexoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    checkpoint_id: UUID
    nome_original: str
    mime_type: str
    tamanho_bytes: int
    storage_key: str
    enviado_por_id: UUID
    created_at: datetime


class AnexoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[AnexoResponse]
    total: int


class AnexoUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    nome_original: str
    mime_type: str
    tamanho_bytes: int
    storage_key: str


class CheckpointStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkpoint: "CheckpointResponse"
    criado: bool


class CheckpointDraftResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkpoint: "CheckpointResponse"
    salvo_em: datetime


class CheckpointSubmitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkpoint: "CheckpointResponse"
    enviado_em: datetime
    proxima_etapa: str | None = None


class CheckpointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    projeto_id: UUID
    tipo: TipoCheckpoint
    status: StatusCheckpoint
    sugerido_em: datetime | None
    iniciado_em: datetime | None
    concluido_em: datetime | None
    respostas_formulario: dict | None
    resumo_para_marketing: str | None
    created_at: datetime
    updated_at: datetime


class CheckpointListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[CheckpointResponse]
    total: int