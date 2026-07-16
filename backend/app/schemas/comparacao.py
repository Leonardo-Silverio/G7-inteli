from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ClassificacaoFarol


class VariacaoScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anterior: float
    atual: float
    diferenca: float
    percentual: float | None
    estavel: bool


class VariacaoCriterio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str
    peso: int
    anterior_nota: float
    atual_nota: float
    diferenca: float
    percentual: float | None
    estavel: bool


class ComparacaoAvaliacaoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avaliacao_anterior_id: UUID
    avaliacao_atual_id: UUID
    checkpoint_id: UUID
    score_alinhamento: VariacaoScore
    score_potencial: VariacaoScore
    criterios_alinhamento: list[VariacaoCriterio]
    criterios_potencial: list[VariacaoCriterio]
    maiores_melhorias: list[VariacaoCriterio]
    maiores_quedas: list[VariacaoCriterio]


class EvolucaoAvaliacaoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avaliacao_id: UUID
    evaluated_at: datetime
    score_alinhamento: float
    score_potencial: float
    classificacao_farol: ClassificacaoFarol
    variacao_alinhamento: VariacaoScore | None = None
    variacao_potencial: VariacaoScore | None = None


class EvolucaoAvaliacaoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkpoint_id: UUID
    items: list[EvolucaoAvaliacaoItem]
    total: int
