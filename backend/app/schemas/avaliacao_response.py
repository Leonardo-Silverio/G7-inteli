from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.schemas.avaliacao import (
    AvaliacaoCalculada,
    ClassificacaoFarol,
    ContribuicaoCriterio,
    CriterioAvaliacao,
    CriteriosAlinhamento,
    CriteriosPotencial,
    FeedbackEstruturado,
)


class AvaliacaoCreateMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    modelo: str = Field(min_length=1, max_length=100)
    prompt_version: str = Field(min_length=1, max_length=100)
    criteria_version: str = Field(min_length=1, max_length=100)
    prompt_hash: str = Field(min_length=64, max_length=64)
    criteria_hash: str = Field(min_length=64, max_length=64)


class AvaliacaoCheckpointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    checkpoint_id: UUID
    score_alinhamento: float
    score_potencial: float
    classificacao_farol: ClassificacaoFarol
    criterios_alinhamento: CriteriosAlinhamento
    criterios_potencial: CriteriosPotencial
    feedback_geral: str
    resumo_para_marketing: str
    evaluation_engine: str
    modelo: str
    prompt_version: str
    criteria_version: str
    evaluated_at: datetime
    prompt_hash: str
    criteria_hash: str
    created_at: datetime
    contribuicoes_alinhamento: list[ContribuicaoCriterio] = Field(default_factory=list)
    contribuicoes_potencial: list[ContribuicaoCriterio] = Field(default_factory=list)
    feedback: Optional[FeedbackEstruturado] = Field(default=None, alias="feedback_json")

    @model_validator(mode="before")
    @classmethod
    def parse_feedback_json(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw = data.get("feedback_json")
            if raw is not None and isinstance(raw, dict):
                data["feedback"] = raw
        else:
            raw = getattr(data, "feedback_json", None)
            if raw is not None and isinstance(raw, dict):
                object.__setattr__(data, "feedback", raw)
        return data


class AvaliacaoHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvaliacaoCheckpointResponse]
    total: int


class AvaliacaoLatestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avaliacao: Optional[AvaliacaoCheckpointResponse] = None
    total_historico: int
