import pytest
from uuid import uuid4
from datetime import datetime

from app.config.settings import settings
from app.ai.provider import FakeAIProvider, AIProviderError, AIInvalidResponseError, AIResponseValidationError
from app.ai.checkpoint_evaluator import CheckpointAIEvaluator
from app.ai.checkpoint_prompt import CheckpointEvaluationContext
from app.models.enums import TipoCheckpoint
from app.schemas.avaliacao import (
    AvaliacaoIAOutput,
    CriterioAvaliacao,
    CriteriosAlinhamento,
    CriteriosPotencial,
)


def _feedback_item_dict(titulo="Item", descricao="Descricao", prioridade="ALTA"):
    return {"titulo": titulo, "descricao": descricao, "evidencias": ["ev"], "prioridade": prioridade}


def _valid_ia_output() -> dict:
    criterio = {
        "nota": 80,
        "feedback": "Bom alinhamento",
        "evidencias": ["ev1"],
        "sugestoes": ["sg1"],
        "confianca": 90,
    }

    alinhamento = {k: criterio for k in [
        "tom_de_voz_azul", "identidade_visual_azul", "posicionamento_malha_regional",
        "uso_correto_produtos_marca", "seguranca_solidez", "clareza_passageiro"
    ]}

    potencial = {k: criterio for k in [
        "pilares_estrategicos_atuais", "receita_produtos_proprios", "alcance_malha_regional",
        "diferenciacao_gol_latam", "recuperacao_fidelizacao_cliente", "viabilidade_operacional"
    ]}

    return {
        "criterios_alinhamento": alinhamento,
        "criterios_potencial": potencial,
        "feedback_geral": "Feedback geral da avaliação",
        "resumo_para_marketing": "Resumo para marketing",
        "pontos_fortes": [_feedback_item_dict("Pf1", "Ponto forte 1")],
        "oportunidades_melhoria": [_feedback_item_dict("Op1", "Oportunidade 1")],
        "recomendacoes_praticas": [_feedback_item_dict("Re1", "Recomendacao 1")],
        "proximos_passos": ["Proximo passo 1"],
        "riscos_principais": [_feedback_item_dict("Ri1", "Risco 1", "BAIXA")],
    }


def _make_context(tipo: TipoCheckpoint = TipoCheckpoint.IDEACAO) -> CheckpointEvaluationContext:
    return CheckpointEvaluationContext(
        checkpoint_id=uuid4(),
        projeto_id=uuid4(),
        tipo_checkpoint=tipo,
        versao_formulario=f"{tipo.value.lower()}_v1",
        versao_business="2026-07",
        schema_version=1,
        respostas={"teste": "valor"},
        anexos=[],
        avaliacoes_anteriores=[],
        conversa_resumida=None,
    )


class TestCheckpointAIEvaluator:
    def test_valid_response_returns_avaliacao_ia_output(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider, modelo=settings.DEEPSEEK_MODEL)

        avaliacao, metadata = evaluator.evaluate(_make_context())

        assert isinstance(avaliacao, AvaliacaoIAOutput)
        assert avaliacao.feedback_geral == "Feedback geral da avaliação"
        assert avaliacao.resumo_para_marketing == "Resumo para marketing"
        assert len(avaliacao.criterios_alinhamento.model_fields) == 6
        assert len(avaliacao.criterios_potencial.model_fields) == 6
        assert len(avaliacao.pontos_fortes) == 1
        assert len(avaliacao.oportunidades_melhoria) == 1
        assert len(avaliacao.recomendacoes_praticas) == 1
        assert len(avaliacao.proximos_passos) == 1
        assert len(avaliacao.riscos_principais) == 1

    def test_missing_criterion_rejected(self):
        invalid_output = _valid_ia_output()
        del invalid_output["criterios_alinhamento"]["tom_de_voz_azul"]

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_extra_criterion_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["criterios_alinhamento"]["criterio_extra"] = {
            "nota": 50, "feedback": "x", "evidencias": [], "sugestoes": [], "confianca": 50
        }

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_invalid_note_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["criterios_alinhamento"]["tom_de_voz_azul"]["nota"] = 150

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_empty_feedback_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["criterios_alinhamento"]["tom_de_voz_azul"]["feedback"] = ""

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_json_with_aggregated_score_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["score_alinhamento"] = 85
        invalid_output["score_potencial"] = 90
        invalid_output["classificacao_farol"] = "PRIORIDADE_MAXIMA"

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_missing_pontos_fortes_rejected(self):
        invalid_output = _valid_ia_output()
        del invalid_output["pontos_fortes"]

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_empty_pontos_fortes_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["pontos_fortes"] = []

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_feedback_item_empty_titulo_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["pontos_fortes"] = [{"titulo": "", "descricao": "desc", "prioridade": "ALTA"}]

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_feedback_item_empty_descricao_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["pontos_fortes"] = [{"titulo": "tit", "descricao": "", "prioridade": "ALTA"}]

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_feedback_item_invalid_prioridade_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["pontos_fortes"] = [{"titulo": "tit", "descricao": "desc", "prioridade": "INVALIDA"}]

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_feedback_item_extra_field_rejected(self):
        invalid_output = _valid_ia_output()
        invalid_output["pontos_fortes"] = [{"titulo": "tit", "descricao": "desc", "extra": "campo"}]

        provider = FakeAIProvider(response=invalid_output)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIResponseValidationError):
            evaluator.evaluate(_make_context())

    def test_provider_error_raises_aiprovider_error(self):
        provider = FakeAIProvider(should_fail=True)
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIProviderError):
            evaluator.evaluate(_make_context())

    def test_non_dict_response_rejected(self):
        provider = FakeAIProvider(response="not a dict")
        evaluator = CheckpointAIEvaluator(provider)

        with pytest.raises(AIInvalidResponseError):
            evaluator.evaluate(_make_context())

    def test_prompt_hash_deterministic(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider)

        context = _make_context()
        _, meta1 = evaluator.evaluate(context)
        _, meta2 = evaluator.evaluate(context)

        assert meta1.prompt_hash == meta2.prompt_hash

    def test_prompt_hash_changes_with_different_prompt(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider)

        _, meta1 = evaluator.evaluate(_make_context(TipoCheckpoint.IDEACAO))
        _, meta2 = evaluator.evaluate(_make_context(TipoCheckpoint.DESENVOLVIMENTO))

        assert meta1.prompt_hash != meta2.prompt_hash

    def test_criteria_hash_deterministic(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider)

        _, meta1 = evaluator.evaluate(_make_context())
        _, meta2 = evaluator.evaluate(_make_context())

        assert meta1.criteria_hash == meta2.criteria_hash

    def test_no_network_call_made(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider)

        evaluator.evaluate(_make_context())

        assert provider.last_system_prompt is not None
        assert provider.last_user_prompt is not None

    def test_evaluator_does_not_call_evaluation_engine(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider)

        avaliacao, _ = evaluator.evaluate(_make_context())

        assert not hasattr(avaliacao, "score_alinhamento")
        assert not hasattr(avaliacao, "score_potencial")
        assert not hasattr(avaliacao, "classificacao_farol")

    def test_evaluator_does_not_access_database(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider)

        avaliacao, metadata = evaluator.evaluate(_make_context())

        assert isinstance(avaliacao, AvaliacaoIAOutput)
        assert metadata.evaluation_engine == "farol-engine-v1"
        assert metadata.modelo == settings.DEEPSEEK_MODEL
        assert metadata.prompt_version == "checkpoint_v2"
        assert metadata.criteria_version == "business_rules_2026_07"
        assert metadata.output_schema_version == "feedback_v1"
        assert len(metadata.prompt_hash) == 64
        assert len(metadata.criteria_hash) == 64

    def test_all_three_checkpoint_types_work(self):
        provider = FakeAIProvider(response=_valid_ia_output())
        evaluator = CheckpointAIEvaluator(provider, modelo=settings.DEEPSEEK_MODEL)

        for tipo in [TipoCheckpoint.IDEACAO, TipoCheckpoint.DESENVOLVIMENTO, TipoCheckpoint.PRE_LANCAMENTO]:
            avaliacao, metadata = evaluator.evaluate(_make_context(tipo))
            assert isinstance(avaliacao, AvaliacaoIAOutput)
            assert metadata.modelo == settings.DEEPSEEK_MODEL
