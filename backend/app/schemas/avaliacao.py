from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.enums import ClassificacaoFarol

class CriterioAvaliacao(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nota: float = Field(ge=0, le=100)
    feedback: str = Field(min_length=1)
    evidencias: list[str] = Field(default_factory=list)
    sugestoes: list[str] = Field(default_factory=list)
    confianca: float | None = Field(default=None, ge=0, le=100)


class CriteriosAlinhamento(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tom_de_voz_azul: CriterioAvaliacao
    identidade_visual_azul: CriterioAvaliacao
    posicionamento_malha_regional: CriterioAvaliacao
    uso_correto_produtos_marca: CriterioAvaliacao
    seguranca_solidez: CriterioAvaliacao
    clareza_passageiro: CriterioAvaliacao


class CriteriosPotencial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pilares_estrategicos_atuais: CriterioAvaliacao
    receita_produtos_proprios: CriterioAvaliacao
    alcance_malha_regional: CriterioAvaliacao
    diferenciacao_gol_latam: CriterioAvaliacao
    recuperacao_fidelizacao_cliente: CriterioAvaliacao
    viabilidade_operacional: CriterioAvaliacao


class AvaliacaoIAOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterios_alinhamento: CriteriosAlinhamento
    criterios_potencial: CriteriosPotencial
    feedback_geral: str = Field(min_length=1)
    resumo_para_marketing: str = Field(min_length=1)


class ContribuicaoCriterio(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str
    nota: float
    peso: int
    contribuicao: float


class AvaliacaoCalculada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    score_alinhamento: float
    score_potencial: float
    classificacao_farol: ClassificacaoFarol
    criterios_alinhamento: CriteriosAlinhamento
    criterios_potencial: CriteriosPotencial
    feedback_geral: str
    resumo_para_marketing: str
    contribuicoes_alinhamento: list[ContribuicaoCriterio] = Field(default_factory=list)
    contribuicoes_potencial: list[ContribuicaoCriterio] = Field(default_factory=list)