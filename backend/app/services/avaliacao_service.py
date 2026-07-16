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
from app.schemas.comparacao import (
    ComparacaoAvaliacaoResponse,
    EvolucaoAvaliacaoResponse,
)
from app.services.evaluation_engine import EvaluationEngine
from app.services.evaluation_comparison_engine import EvaluationComparisonEngine
from app.services.feedback_builder import FeedbackBuilder


class CheckpointNotFoundError(ValueError):
    pass


class CriteriaVersionMismatchError(ValueError):
    pass


class NotEnoughEvaluationsError(ValueError):
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
        self.comparison_engine = EvaluationComparisonEngine()

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

        feedback_json = FeedbackBuilder.montar_feedback_json(
            calculada,
            pontos_fortes=ia_output.pontos_fortes,
            oportunidades_melhoria=ia_output.oportunidades_melhoria,
            recomendacoes_praticas=ia_output.recomendacoes_praticas,
            proximos_passos=ia_output.proximos_passos,
            riscos_principais=ia_output.riscos_principais,
        )

        avaliacao = AvaliacaoCheckpoint(
            checkpoint_id=checkpoint_id,
            score_alinhamento=int(round(calculada.score_alinhamento)),
            score_potencial=int(round(calculada.score_potencial)),
            classificacao_farol=calculada.classificacao_farol,
            criterios_alinhamento=calculada.criterios_alinhamento.model_dump(),
            criterios_potencial=calculada.criterios_potencial.model_dump(),
            feedback_geral=ia_output.feedback_geral,
            resumo_para_marketing=ia_output.resumo_para_marketing,
            feedback_json=feedback_json,
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

    def compare_evaluations(
        self, atual_id: UUID, anterior_id: UUID
    ) -> ComparacaoAvaliacaoResponse:
        atual = self.avaliacao_repo.get_evaluation(atual_id)
        anterior = self.avaliacao_repo.get_evaluation(anterior_id)
        if not atual or not anterior:
            raise CheckpointNotFoundError("Avaliação não encontrada")
        if atual.criteria_version != anterior.criteria_version:
            raise CriteriaVersionMismatchError(
                "Versão dos critérios diferente entre as avaliações"
            )
        return self.comparison_engine.comparar(
            anterior_id=anterior.id,
            atual_id=atual.id,
            checkpoint_id=atual.checkpoint_id,
            criterios_alinhamento_anterior=anterior.criterios_alinhamento or {},
            criterios_potencial_anterior=anterior.criterios_potencial or {},
            criterios_alinhamento_atual=atual.criterios_alinhamento or {},
            criterios_potencial_atual=atual.criterios_potencial or {},
        )

    def compare_latest_with_previous(
        self, checkpoint_id: UUID
    ) -> ComparacaoAvaliacaoResponse:
        avaliacoes = self.avaliacao_repo.list_evaluations(checkpoint_id)
        if len(avaliacoes) < 2:
            raise NotEnoughEvaluationsError(
                "São necessárias pelo menos 2 avaliações para comparação"
            )
        atual = avaliacoes[0]
        anterior = avaliacoes[1]
        if atual.criteria_version != anterior.criteria_version:
            raise CriteriaVersionMismatchError(
                "Versão dos critérios diferente entre as avaliações"
            )
        return self.comparison_engine.comparar(
            anterior_id=anterior.id,
            atual_id=atual.id,
            checkpoint_id=checkpoint_id,
            criterios_alinhamento_anterior=anterior.criterios_alinhamento or {},
            criterios_potencial_anterior=anterior.criterios_potencial or {},
            criterios_alinhamento_atual=atual.criterios_alinhamento or {},
            criterios_potencial_atual=atual.criterios_potencial or {},
        )

    def get_evolution(self, checkpoint_id: UUID) -> EvolucaoAvaliacaoResponse:
        avaliacoes = self.avaliacao_repo.list_evaluations(checkpoint_id)
        historico = []
        for a in reversed(avaliacoes):
            score_alinhamento = self.comparison_engine._calcular_score(
                a.criterios_alinhamento or {},
                self.comparison_engine.PESOS_ALINHAMENTO,
            )
            score_potencial = self.comparison_engine._calcular_score(
                a.criterios_potencial or {},
                self.comparison_engine.PESOS_POTENCIAL,
            )
            historico.append(
                {
                    "avaliacao_id": a.id,
                    "evaluated_at": a.evaluated_at,
                    "score_alinhamento": score_alinhamento,
                    "score_potencial": score_potencial,
                    "classificacao_farol": a.classificacao_farol,
                }
            )
        return self.comparison_engine.resumo_evolucao(checkpoint_id, historico)

    def _to_response(self, avaliacao: AvaliacaoCheckpoint) -> AvaliacaoCheckpointResponse:
        return AvaliacaoCheckpointResponse.model_validate(avaliacao, from_attributes=True)
