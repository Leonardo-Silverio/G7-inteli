import hashlib
import pytest

from app.ai.checkpoint_prompt import (
    build_prompt,
    calculate_prompt_hash,
    calculate_criteria_hash,
    CheckpointEvaluationContext,
    PROMPT_VERSION,
    CRITERIA_VERSION,
    SYSTEM_PROMPT_BASE,
)
from app.schemas.avaliacao import AvaliacaoIAOutput, CriteriosAlinhamento, CriteriosPotencial
from app.models.enums import TipoCheckpoint


def _make_context(tipo: TipoCheckpoint) -> CheckpointEvaluationContext:
    from uuid import uuid4
    from datetime import datetime

    return CheckpointEvaluationContext(
        checkpoint_id=uuid4(),
        projeto_id=uuid4(),
        tipo_checkpoint=tipo,
        versao_formulario=f"{tipo.value.lower()}_v1",
        versao_business="2026-07",
        schema_version=1,
        respostas={"campo_teste": "valor_teste"},
        anexos=[],
        avaliacoes_anteriores=[],
        conversa_resumida=None,
    )


class TestPromptBuilding:
    def test_prompt_ideacao_contains_keywords(self):
        context = _make_context(TipoCheckpoint.IDEACAO)
        system, user = build_prompt(context)

        assert "IDEAÇÃO" in user.upper() or "Ideação" in user
        assert "problema" in user.lower() or "oportunidade" in user.lower()
        assert "solução" in user.lower() or "proposta" in user.lower()
        assert "foco estratégico" in user.lower() or "foco azul" in user.lower()
        assert "impacto regional" in user.lower() or "malha regional" in user.lower()
        assert "duplicação" in user.lower() or "semelhante" in user.lower()
        assert "prazo" in user.lower() or "mercado" in user.lower()
        assert "dependência" in user.lower() or "crítica" in user.lower()
        assert "diferenciação" in user.lower() or "diferencial" in user.lower()
        assert "informação" in (system + user).lower() or "compartilhada" in (system + user).lower()

    def test_prompt_desenvolvimento_contains_keywords(self):
        context = _make_context(TipoCheckpoint.DESENVOLVIMENTO)
        system, user = build_prompt(context)

        assert "DESENVOLVIMENTO" in user.upper() or "Desenvolvimento" in user
        assert "material desenvolvido" in user.lower()
        assert "produto" in user.lower() and "marca" in user.lower()
        assert "tom" in user.lower() or "comunicação" in user.lower()
        assert "mudança" in user.lower() or "ideação" in user.lower()
        assert "feedback" in user.lower()
        assert "limitação" in user.lower() or "interna" in user.lower()

    def test_prompt_pre_lancamento_contains_keywords(self):
        context = _make_context(TipoCheckpoint.PRE_LANCAMENTO)
        system, user = build_prompt(context)

        assert "PRÉ-LANÇAMENTO" in user.upper() or "Pré-Lançamento" in user or "Pre-Lancamento" in user
        assert "material final" in user.lower() or "versão final" in user.lower()
        assert "área" in user.lower() and "envolvida" in user.lower()
        assert "dado" in user.lower() and "cliente" in user.lower()
        assert "jurídico" in user.lower() or "compliance" in user.lower() or "revisão" in user.lower()
        assert "tarifa" in user.lower() or "benefício" in user.lower() or "condição" in user.lower()
        assert "risco" in user.lower() and "interpretação" in user.lower()
        assert "campanha" in user.lower() or "conflito" in user.lower()
        assert "data" in user.lower() and "prevista" in user.lower()
        assert "risco" in user.lower() and "final" in user.lower()

    def test_alignment_criteria_present_in_prompt(self):
        for tipo in [TipoCheckpoint.IDEACAO, TipoCheckpoint.DESENVOLVIMENTO, TipoCheckpoint.PRE_LANCAMENTO]:
            context = _make_context(tipo)
            system, user = build_prompt(context)

            for criterio in [
                "tom_de_voz_azul", "identidade_visual_azul", "posicionamento_malha_regional",
                "uso_correto_produtos_marca", "seguranca_solidez", "clareza_passageiro"
            ]:
                assert criterio in system

    def test_potential_criteria_present_in_prompt(self):
        for tipo in [TipoCheckpoint.IDEACAO, TipoCheckpoint.DESENVOLVIMENTO, TipoCheckpoint.PRE_LANCAMENTO]:
            context = _make_context(tipo)
            system, user = build_prompt(context)

            for criterio in [
                "pilares_estrategicos_atuais", "receita_produtos_proprios", "alcance_malha_regional",
                "diferenciacao_gol_latam", "recuperacao_fidelizacao_cliente", "viabilidade_operacional"
            ]:
                assert criterio in system

    def test_prompt_forbids_ai_scores(self):
        for tipo in [TipoCheckpoint.IDEACAO, TipoCheckpoint.DESENVOLVIMENTO, TipoCheckpoint.PRE_LANCAMENTO]:
            context = _make_context(tipo)
            system, user = build_prompt(context)

            full = system + user
            assert "não deve" in full.lower() or "não inclua" in full.lower() or "proibido" in full.lower()
            assert "score_alinhamento" in full.lower() or "score_potencial" in full.lower() or "classificacao_farol" in full.lower()

    def test_privacy_rules_in_system_prompt(self):
        context = _make_context(TipoCheckpoint.IDEACAO)
        system, user = build_prompt(context)

        assert "privacidade" in system.lower() or "privado" in system.lower() or "sensível" in system.lower()
        assert "marketing" in system.lower()
        assert "conversa" in system.lower() or "bruta" in system.lower()


class TestPromptHash:
    def test_prompt_hash_deterministic(self):
        context = _make_context(TipoCheckpoint.IDEACAO)
        system, user = build_prompt(context)

        h1 = calculate_prompt_hash(system, user)
        h2 = calculate_prompt_hash(system, user)

        assert h1 == h2
        assert len(h1) == 64

    def test_prompt_hash_changes_with_content(self):
        context1 = _make_context(TipoCheckpoint.IDEACAO)
        system1, user1 = build_prompt(context1)

        context2 = _make_context(TipoCheckpoint.DESENVOLVIMENTO)
        system2, user2 = build_prompt(context2)

        h1 = calculate_prompt_hash(system1, user1)
        h2 = calculate_prompt_hash(system2, user2)

        assert h1 != h2

    def test_criteria_hash_deterministic(self):
        h1 = calculate_criteria_hash()
        h2 = calculate_criteria_hash()

        assert h1 == h2
        assert len(h1) == 64

    def test_criteria_hash_is_sha256(self):
        h = calculate_criteria_hash()
        # Verify it's valid hex
        int(h, 16)

    def test_prompt_contains_pontos_fortes_instruction(self):
        for tipo in [TipoCheckpoint.IDEACAO, TipoCheckpoint.DESENVOLVIMENTO, TipoCheckpoint.PRE_LANCAMENTO]:
            context = _make_context(tipo)
            system, user = build_prompt(context)
            full = system + user
            assert "pontos_fortes" in full.lower()
            assert "oportunidades_melhoria" in full.lower()
            assert "recomendacoes_praticas" in full.lower()
            assert "proximos_passos" in full
            assert "riscos_principais" in full

    def test_prompt_requires_structured_feedback_items(self):
        context = _make_context(TipoCheckpoint.IDEACAO)
        system, user = build_prompt(context)
        full = system + user
        assert "titulo" in full.lower()
        assert "descricao" in full.lower()
        assert "prioridade" in full.lower()

    def test_prompt_still_forbids_ai_score_and_classification(self):
        context = _make_context(TipoCheckpoint.IDEACAO)
        system, user = build_prompt(context)
        full = system + user
        assert "não inclua" in full.lower() or "não calcule" in full.lower()
        assert "score_alinhamento" in full
        assert "classificacao_farol" in full