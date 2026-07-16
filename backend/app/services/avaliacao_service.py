from uuid import UUID
from datetime import datetime, timezone

from app.models.checkpoint import AvaliacaoCheckpoint
from app.repositories.avaliacao_repository import AvaliacaoRepository
from app.repositories.checkpoint_repository import CheckpointRepository
from app.schemas.avaliacao import AvaliacaoCalculada, AvaliacaoIAOutput
from app.schemas.avaliacao_response import (
    AvaliacaoCheckpointResponse,
    AvaliacaoHistoryResponse,
    AvaliacaoLatestResponse,
)
from app.services.evaluation_engine import EvaluationEngine


class CheckpointNotFoundError(ValueError):
    pass


class AvaliacaoService:
    def __init__(
        self,
        avaliacao_repo: AvaliacaoRepository,
        checkpoint_repo: CheckpointRepository,
    ):
        self.avaliacao_repo = avaliacao_repo
        self.checkpoint_repo = checkpoint_repo
        self.engine = EvaluationEngine()

    def create_evaluation(
        self,
        checkpoint_id: UUID,
        ia_output: AvaliacaoIAOutput,
        modelo: str,
        prompt_version: str,
        criteria_version: str,
        prompt_hash: str,
        criteria_hash: str,
    ) -> AvaliacaoCheckpointResponse:
        checkpoint = self.checkpoint_repo.get_checkpoint_by_id(checkpoint_id)
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        calculada = self.engine.evaluate(ia_output)

        avaliacao = AvaliacaoCheckpoint(
            checkpoint_id=checkpoint_id,
            score_alinhamento=int(round(calculada.score_alinhamento)),
            score_potencial=int(round(calculada.score_potencial)),
            classificacao_farol=calculada.classificacao_farol,
            criterios_alinhamento=calculada.criterios_alinhamento.model_dump(),
            criterios_potencial=calculada.criterios_potencial.model_dump(),
            feedback_geral=ia_output.feedback_geral,
            resumo_para_marketing=ia_output.resumo_para_marketing,
            evaluation_engine="farol-engine-v1",
            modelo=modelo,
            prompt_version=prompt_version,
            criteria_version=criteria_version,
            evaluated_at=datetime.now(timezone.utc),
            prompt_hash=prompt_hash,
            criteria_hash=criteria_hash,
        )

        self.avaliacao_repo.create_evaluation(avaliacao)

        return self._to_response(avaliacao)

    def get_latest(self, checkpoint_id: UUID) -> AvaliacaoLatestResponse:
        avaliacao = self.avaliacao_repo.get_latest_evaluation(checkpoint_id)
        total = self.avaliacao_repo.count_evaluations(checkpoint_id)

        if not avaliacao:
            return AvaliacaoLatestResponse(avaliacao=None, total_historico=total)

        return AvaliacaoLatestResponse(
            avaliacao=self._to_response(avaliacao),
            total_historico=total,
        )

    def list_history(self, checkpoint_id: UUID) -> AvaliacaoHistoryResponse:
        avaliacoes = self.avaliacao_repo.list_evaluations(checkpoint_id)
        total = self.avaliacao_repo.count_evaluations(checkpoint_id)

        return AvaliacaoHistoryResponse(
            items=[self._to_response(a) for a in avaliacoes],
            total=total,
        )

    def _to_response(self, avaliacao: AvaliacaoCheckpoint) -> AvaliacaoCheckpointResponse:
        return AvaliacaoCheckpointResponse.model_validate(avaliacao, from_attributes=True)