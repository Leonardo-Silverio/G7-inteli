import pytest
from uuid import UUID
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.comparacao import (
    ComparacaoAvaliacaoResponse,
    EvolucaoAvaliacaoItem,
    EvolucaoAvaliacaoResponse,
    VariacaoCriterio,
    VariacaoScore,
)
from app.services.evaluation_comparison_engine import EvaluationComparisonEngine
from app.models.enums import ClassificacaoFarol


def _criterio_dict(nota: float) -> dict:
    return {"nota": nota, "feedback": "Ok", "evidencias": [], "sugestoes": [], "confianca": 90}


def _alinhamento_dicts(nota: float) -> dict:
    c = _criterio_dict(nota)
    return {
        "tom_de_voz_azul": c,
        "identidade_visual_azul": c,
        "posicionamento_malha_regional": c,
        "uso_correto_produtos_marca": c,
        "seguranca_solidez": c,
        "clareza_passageiro": c,
    }


def _potencial_dicts(nota: float) -> dict:
    c = _criterio_dict(nota)
    return {
        "pilares_estrategicos_atuais": c,
        "receita_produtos_proprios": c,
        "alcance_malha_regional": c,
        "diferenciacao_gol_latam": c,
        "recuperacao_fidelizacao_cliente": c,
        "viabilidade_operacional": c,
    }


class TestEvaluationComparisonEngine:
    def test_calcular_score_todos_100(self):
        score = EvaluationComparisonEngine._calcular_score(
            _alinhamento_dicts(100), EvaluationComparisonEngine.PESOS_ALINHAMENTO
        )
        assert score == 100.0

    def test_calcular_score_todos_0(self):
        score = EvaluationComparisonEngine._calcular_score(
            _alinhamento_dicts(0), EvaluationComparisonEngine.PESOS_POTENCIAL
        )
        assert score == 0.0

    def test_calcular_score_notas_diferentes(self):
        alinhamento = {
            "tom_de_voz_azul": _criterio_dict(80),
            "identidade_visual_azul": _criterio_dict(90),
            "posicionamento_malha_regional": _criterio_dict(70),
            "uso_correto_produtos_marca": _criterio_dict(60),
            "seguranca_solidez": _criterio_dict(50),
            "clareza_passageiro": _criterio_dict(40),
        }
        score = EvaluationComparisonEngine._calcular_score(
            alinhamento, EvaluationComparisonEngine.PESOS_ALINHAMENTO
        )
        expected = round(
            80 * 0.25 + 90 * 0.20 + 70 * 0.20 + 60 * 0.15 + 50 * 0.10 + 40 * 0.10, 2
        )
        assert score == expected

    def test_calcular_score_criterio_ausente_default_zero(self):
        score = EvaluationComparisonEngine._calcular_score(
            {}, EvaluationComparisonEngine.PESOS_ALINHAMENTO
        )
        assert score == 0.0

    def test_calcular_score_matches_evaluation_engine(self):
        from app.schemas.avaliacao import CriterioAvaliacao, CriteriosAlinhamento
        from app.services.evaluation_engine import EvaluationEngine

        c = CriterioAvaliacao(nota=75, feedback="Ok")
        criterios_model = CriteriosAlinhamento(
            tom_de_voz_azul=c, identidade_visual_azul=c,
            posicionamento_malha_regional=c, uso_correto_produtos_marca=c,
            seguranca_solidez=c, clareza_passageiro=c,
        )
        engine_score = EvaluationEngine.calculate_alignment(criterios_model)

        comp_score = EvaluationComparisonEngine._calcular_score(
            _alinhamento_dicts(75), EvaluationComparisonEngine.PESOS_ALINHAMENTO
        )
        assert comp_score == engine_score

    def test_compute_variacao_score_aumento(self):
        v = EvaluationComparisonEngine._compute_variacao_score(70.0, 85.0)
        assert v.anterior == 70.0
        assert v.atual == 85.0
        assert v.diferenca == 15.0
        assert v.percentual == pytest.approx(21.43, rel=0.01)
        assert v.estavel is False

    def test_compute_variacao_score_queda(self):
        v = EvaluationComparisonEngine._compute_variacao_score(90.0, 75.0)
        assert v.diferenca == -15.0
        assert v.percentual == pytest.approx(-16.67, rel=0.01)
        assert v.estavel is False

    def test_compute_variacao_score_zero_anterior(self):
        v = EvaluationComparisonEngine._compute_variacao_score(0.0, 80.0)
        assert v.diferenca == 80.0
        assert v.percentual is None
        assert v.estavel is False

    def test_compute_variacao_score_estavel(self):
        v = EvaluationComparisonEngine._compute_variacao_score(75.0, 75.0)
        assert v.diferenca == 0.0
        assert v.percentual == 0.0
        assert v.estavel is True

    def test_compute_variacao_score_estavel_limiar(self):
        v = EvaluationComparisonEngine._compute_variacao_score(75.0, 75.004)
        assert abs(v.diferenca) < 0.01
        assert v.estavel is True

    def test_compute_variacao_score_sem_mudanca(self):
        v = EvaluationComparisonEngine._compute_variacao_score(75.0, 75.0)
        assert v.diferenca == 0.0
        assert v.percentual == 0.0
        assert v.estavel is True

    def test_compute_variacao_criterio_aumento(self):
        v = EvaluationComparisonEngine._compute_variacao_criterio(
            "tom_de_voz_azul", 25, 70.0, 90.0
        )
        assert v.nome == "tom_de_voz_azul"
        assert v.peso == 25
        assert v.anterior_nota == 70.0
        assert v.atual_nota == 90.0
        assert v.diferenca == 20.0
        assert v.percentual == pytest.approx(28.57, rel=0.01)
        assert v.estavel is False

    def test_compute_variacao_criterio_zero_anterior(self):
        v = EvaluationComparisonEngine._compute_variacao_criterio(
            "clareza_passageiro", 10, 0.0, 80.0
        )
        assert v.diferenca == 80.0
        assert v.percentual is None

    def test_compute_variacao_criterio_estavel(self):
        v = EvaluationComparisonEngine._compute_variacao_criterio(
            "seguranca_solidez", 10, 50.0, 50.0
        )
        assert v.diferenca == 0.0
        assert v.estavel is True

    def test_comparar_melhorou_geral(self):
        anterior_id = UUID("00000000-0000-0000-0000-000000000001")
        atual_id = UUID("00000000-0000-0000-0000-000000000002")
        checkpoint_id = UUID("00000000-0000-0000-0000-000000000003")

        result = EvaluationComparisonEngine.comparar(
            anterior_id=anterior_id,
            atual_id=atual_id,
            checkpoint_id=checkpoint_id,
            criterios_alinhamento_anterior=_alinhamento_dicts(60),
            criterios_potencial_anterior=_potencial_dicts(60),
            criterios_alinhamento_atual=_alinhamento_dicts(80),
            criterios_potencial_atual=_potencial_dicts(80),
        )

        assert result.avaliacao_anterior_id == anterior_id
        assert result.avaliacao_atual_id == atual_id
        assert result.checkpoint_id == checkpoint_id
        assert result.score_alinhamento.atual == 80.0
        assert result.score_alinhamento.anterior == 60.0
        assert result.score_alinhamento.diferenca == 20.0
        assert result.score_potencial.atual == 80.0
        assert result.score_potencial.anterior == 60.0
        assert result.score_potencial.diferenca == 20.0
        assert len(result.criterios_alinhamento) == 6
        assert len(result.criterios_potencial) == 6

    def test_comparar_piorou_geral(self):
        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(80),
            criterios_potencial_anterior=_potencial_dicts(80),
            criterios_alinhamento_atual=_alinhamento_dicts(50),
            criterios_potencial_atual=_potencial_dicts(50),
        )

        assert result.score_alinhamento.diferenca == -30.0
        assert result.score_potencial.diferenca == -30.0
        assert result.score_alinhamento.estavel is False

    def test_comparar_sem_mudanca(self):
        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(75),
            criterios_potencial_anterior=_potencial_dicts(75),
            criterios_alinhamento_atual=_alinhamento_dicts(75),
            criterios_potencial_atual=_potencial_dicts(75),
        )

        assert result.score_alinhamento.diferenca == 0.0
        assert result.score_alinhamento.estavel is True
        assert result.score_potencial.estavel is True

    def test_comparar_maiores_melhorias(self):
        criterios_anteriores = {
            "tom_de_voz_azul": _criterio_dict(50),
            "identidade_visual_azul": _criterio_dict(60),
            "posicionamento_malha_regional": _criterio_dict(70),
            "uso_correto_produtos_marca": _criterio_dict(40),
            "seguranca_solidez": _criterio_dict(80),
            "clareza_passageiro": _criterio_dict(90),
        }
        criterios_atuais = {
            "tom_de_voz_azul": _criterio_dict(90),
            "identidade_visual_azul": _criterio_dict(85),
            "posicionamento_malha_regional": _criterio_dict(75),
            "uso_correto_produtos_marca": _criterio_dict(45),
            "seguranca_solidez": _criterio_dict(80),
            "clareza_passageiro": _criterio_dict(90),
        }

        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=criterios_anteriores,
            criterios_potencial_anterior=_potencial_dicts(70),
            criterios_alinhamento_atual=criterios_atuais,
            criterios_potencial_atual=_potencial_dicts(70),
        )

        assert len(result.maiores_melhorias) == 3
        for m in result.maiores_melhorias:
            assert m.diferenca > 0
        assert result.maiores_melhorias[0].nome == "tom_de_voz_azul"
        assert result.maiores_melhorias[0].diferenca == 40.0
        assert result.maiores_melhorias[1].nome == "identidade_visual_azul"
        assert result.maiores_melhorias[2].nome == "posicionamento_malha_regional"
        assert result.maiores_quedas == []

    def test_comparar_maiores_quedas(self):
        criterios_anteriores = {
            "tom_de_voz_azul": _criterio_dict(90),
            "identidade_visual_azul": _criterio_dict(80),
            "posicionamento_malha_regional": _criterio_dict(50),
            "uso_correto_produtos_marca": _criterio_dict(60),
            "seguranca_solidez": _criterio_dict(70),
            "clareza_passageiro": _criterio_dict(40),
        }
        criterios_atuais = {
            "tom_de_voz_azul": _criterio_dict(50),
            "identidade_visual_azul": _criterio_dict(55),
            "posicionamento_malha_regional": _criterio_dict(45),
            "uso_correto_produtos_marca": _criterio_dict(55),
            "seguranca_solidez": _criterio_dict(70),
            "clareza_passageiro": _criterio_dict(40),
        }

        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=criterios_anteriores,
            criterios_potencial_anterior=_potencial_dicts(70),
            criterios_alinhamento_atual=criterios_atuais,
            criterios_potencial_atual=_potencial_dicts(70),
        )

        assert len(result.maiores_quedas) == 3
        for m in result.maiores_quedas:
            assert m.diferenca < 0
        assert result.maiores_quedas[0].nome == "posicionamento_malha_regional"
        assert result.maiores_quedas[0].diferenca == -5.0

    def test_comparar_maiores_apenas_melhorias(self):
        criterios_anteriores = {
            "tom_de_voz_azul": _criterio_dict(50),
            "posicionamento_malha_regional": _criterio_dict(50),
        }
        criterios_atuais = {
            "tom_de_voz_azul": _criterio_dict(90),
            "posicionamento_malha_regional": _criterio_dict(90),
        }
        for key in ["identidade_visual_azul", "uso_correto_produtos_marca",
                     "seguranca_solidez", "clareza_passageiro"]:
            criterios_anteriores[key] = _criterio_dict(50)
            criterios_atuais[key] = _criterio_dict(50)

        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=criterios_anteriores,
            criterios_potencial_anterior=_potencial_dicts(70),
            criterios_alinhamento_atual=criterios_atuais,
            criterios_potencial_atual=_potencial_dicts(70),
        )

        assert len(result.maiores_melhorias) == 2
        assert len(result.maiores_quedas) == 0
        assert result.maiores_melhorias[0].nome == "tom_de_voz_azul"

    def test_comparar_limite_tres_melhorias(self):
        criterios_anteriores = _alinhamento_dicts(50)
        criterios_atuais = _alinhamento_dicts(90)
        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=criterios_anteriores,
            criterios_potencial_anterior=_potencial_dicts(50),
            criterios_alinhamento_atual=criterios_atuais,
            criterios_potencial_atual=_potencial_dicts(90),
        )

        assert len(result.maiores_melhorias) <= 3
        for m in result.maiores_melhorias:
            assert m.diferenca > 0

    def test_comparar_estaveis_excluidos_melhorias(self):
        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(75),
            criterios_potencial_anterior=_potencial_dicts(75),
            criterios_alinhamento_atual=_alinhamento_dicts(75),
            criterios_potencial_atual=_potencial_dicts(75),
        )

        assert result.maiores_melhorias == []
        assert result.maiores_quedas == []

    def test_comparar_arredondamento_duas_casas(self):
        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(33.333),
            criterios_potencial_anterior=_potencial_dicts(33.333),
            criterios_alinhamento_atual=_alinhamento_dicts(66.667),
            criterios_potencial_atual=_potencial_dicts(66.667),
        )

        assert result.score_alinhamento.diferenca == round(result.score_alinhamento.diferenca, 2)
        assert result.score_potencial.diferenca == round(result.score_potencial.diferenca, 2)
        for c in result.criterios_alinhamento:
            assert c.diferenca == round(c.diferenca, 2)
            if c.percentual is not None:
                assert c.percentual == round(c.percentual, 2)

    def test_comparar_criterios_alinhamento_posicao_correta(self):
        result = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(70),
            criterios_potencial_anterior=_potencial_dicts(60),
            criterios_alinhamento_atual=_alinhamento_dicts(80),
            criterios_potencial_atual=_potencial_dicts(90),
        )

        nomes_alinhamento = [c.nome for c in result.criterios_alinhamento]
        assert nomes_alinhamento == [
            "tom_de_voz_azul", "identidade_visual_azul",
            "posicionamento_malha_regional", "uso_correto_produtos_marca",
            "seguranca_solidez", "clareza_passageiro",
        ]
        nomes_potencial = [c.nome for c in result.criterios_potencial]
        assert nomes_potencial == [
            "pilares_estrategicos_atuais", "receita_produtos_proprios",
            "alcance_malha_regional", "diferenciacao_gol_latam",
            "recuperacao_fidelizacao_cliente", "viabilidade_operacional",
        ]

    def test_resumo_evolucao_vazia(self):
        result = EvaluationComparisonEngine.resumo_evolucao(
            UUID(int=1), []
        )
        assert result.checkpoint_id == UUID(int=1)
        assert result.items == []
        assert result.total == 0

    def test_resumo_evolucao_unico_item(self):
        now = datetime.now(timezone.utc)
        result = EvaluationComparisonEngine.resumo_evolucao(
            UUID(int=1),
            [
                {
                    "avaliacao_id": UUID(int=10),
                    "evaluated_at": now,
                    "score_alinhamento": 75.0,
                    "score_potencial": 65.0,
                    "classificacao_farol": ClassificacaoFarol.VALE_INVESTIR_TEMPO,
                }
            ],
        )

        assert result.total == 1
        assert result.items[0].avaliacao_id == UUID(int=10)
        assert result.items[0].score_alinhamento == 75.0
        assert result.items[0].variacao_alinhamento is None
        assert result.items[0].variacao_potencial is None

    def test_resumo_evolucao_dois_itens(self):
        now = datetime.now(timezone.utc)
        result = EvaluationComparisonEngine.resumo_evolucao(
            UUID(int=1),
            [
                {
                    "avaliacao_id": UUID(int=10),
                    "evaluated_at": now,
                    "score_alinhamento": 60.0,
                    "score_potencial": 50.0,
                    "classificacao_farol": ClassificacaoFarol.BAIXA_PRIORIDADE,
                },
                {
                    "avaliacao_id": UUID(int=20),
                    "evaluated_at": now,
                    "score_alinhamento": 80.0,
                    "score_potencial": 70.0,
                    "classificacao_farol": ClassificacaoFarol.PRIORIDADE_MAXIMA,
                },
            ],
        )

        assert result.total == 2
        assert result.items[0].variacao_alinhamento is None
        assert result.items[0].variacao_potencial is None

        assert result.items[1].variacao_alinhamento is not None
        assert result.items[1].variacao_alinhamento.anterior == 60.0
        assert result.items[1].variacao_alinhamento.atual == 80.0
        assert result.items[1].variacao_alinhamento.diferenca == 20.0
        assert result.items[1].variacao_potencial is not None
        assert result.items[1].variacao_potencial.diferenca == 20.0

    def test_resumo_evolucao_tres_itens(self):
        now = datetime.now(timezone.utc)
        result = EvaluationComparisonEngine.resumo_evolucao(
            UUID(int=1),
            [
                {
                    "avaliacao_id": UUID(int=10),
                    "evaluated_at": now,
                    "score_alinhamento": 50.0,
                    "score_potencial": 40.0,
                    "classificacao_farol": ClassificacaoFarol.BAIXA_PRIORIDADE,
                },
                {
                    "avaliacao_id": UUID(int=20),
                    "evaluated_at": now,
                    "score_alinhamento": 70.0,
                    "score_potencial": 60.0,
                    "classificacao_farol": ClassificacaoFarol.VALE_INVESTIR_TEMPO,
                },
                {
                    "avaliacao_id": UUID(int=30),
                    "evaluated_at": now,
                    "score_alinhamento": 90.0,
                    "score_potencial": 80.0,
                    "classificacao_farol": ClassificacaoFarol.PRIORIDADE_MAXIMA,
                },
            ],
        )

        assert result.total == 3
        assert result.items[0].variacao_alinhamento is None
        assert result.items[1].variacao_alinhamento is not None
        assert result.items[1].variacao_alinhamento.diferenca == 20.0
        assert result.items[2].variacao_alinhamento.diferenca == 20.0
        assert result.items[2].variacao_potencial.diferenca == 20.0

    def test_engine_deterministico(self):
        r1 = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(60),
            criterios_potencial_anterior=_potencial_dicts(55),
            criterios_alinhamento_atual=_alinhamento_dicts(75),
            criterios_potencial_atual=_potencial_dicts(80),
        )
        r2 = EvaluationComparisonEngine.comparar(
            anterior_id=UUID(int=1),
            atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            criterios_alinhamento_anterior=_alinhamento_dicts(60),
            criterios_potencial_anterior=_potencial_dicts(55),
            criterios_alinhamento_atual=_alinhamento_dicts(75),
            criterios_potencial_atual=_potencial_dicts(80),
        )

        assert r1.score_alinhamento.diferenca == r2.score_alinhamento.diferenca
        assert r1.score_potencial.diferenca == r2.score_potencial.diferenca
        assert r1.maiores_melhorias == r2.maiores_melhorias
        assert r1.maiores_quedas == r2.maiores_quedas

    def test_engine_nao_chama_ia(self):
        assert not hasattr(EvaluationComparisonEngine, "evaluate")
        assert not hasattr(EvaluationComparisonEngine, "create_evaluation")


class TestComparacaoSchemas:
    def test_variacao_score_valido(self):
        v = VariacaoScore(anterior=70.0, atual=85.0, diferenca=15.0, percentual=21.43, estavel=False)
        assert v.anterior == 70.0
        assert v.atual == 85.0
        assert v.diferenca == 15.0
        assert v.percentual == 21.43
        assert v.estavel is False

    def test_variacao_score_percentual_none(self):
        v = VariacaoScore(anterior=0.0, atual=80.0, diferenca=80.0, percentual=None, estavel=False)
        assert v.percentual is None

    def test_variacao_score_extra_rejeitado(self):
        with pytest.raises(ValidationError):
            VariacaoScore(anterior=70.0, atual=85.0, diferenca=15.0, percentual=21.43, estavel=False, extra="x")

    def test_variacao_criterio_valido(self):
        v = VariacaoCriterio(
            nome="tom_de_voz_azul", peso=25, anterior_nota=70.0, atual_nota=90.0,
            diferenca=20.0, percentual=28.57, estavel=False,
        )
        assert v.nome == "tom_de_voz_azul"
        assert v.peso == 25
        assert v.anterior_nota == 70.0
        assert v.atual_nota == 90.0

    def test_variacao_criterio_extra_rejeitado(self):
        with pytest.raises(ValidationError):
            VariacaoCriterio(
                nome="x", peso=10, anterior_nota=50.0, atual_nota=60.0,
                diferenca=10.0, percentual=20.0, estavel=False, extra="x",
            )

    def test_comparacao_response_valida(self):
        v1 = VariacaoScore(anterior=60.0, atual=80.0, diferenca=20.0, percentual=33.33, estavel=False)
        v2 = VariacaoScore(anterior=60.0, atual=80.0, diferenca=20.0, percentual=33.33, estavel=False)
        c = VariacaoCriterio(
            nome="tom_de_voz_azul", peso=25, anterior_nota=60.0, atual_nota=80.0,
            diferenca=20.0, percentual=33.33, estavel=False,
        )

        result = ComparacaoAvaliacaoResponse(
            avaliacao_anterior_id=UUID(int=1),
            avaliacao_atual_id=UUID(int=2),
            checkpoint_id=UUID(int=3),
            score_alinhamento=v1,
            score_potencial=v2,
            criterios_alinhamento=[c],
            criterios_potencial=[c],
            maiores_melhorias=[c],
            maiores_quedas=[],
        )
        assert result.avaliacao_anterior_id == UUID(int=1)
        assert result.avaliacao_atual_id == UUID(int=2)
        assert len(result.criterios_alinhamento) == 1
        assert len(result.maiores_melhorias) == 1
        assert result.maiores_quedas == []

    def test_evolucao_item_valido(self):
        now = datetime.now(timezone.utc)
        item = EvolucaoAvaliacaoItem(
            avaliacao_id=UUID(int=10),
            evaluated_at=now,
            score_alinhamento=75.0,
            score_potencial=65.0,
            classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
        )
        assert item.variacao_alinhamento is None
        assert item.variacao_potencial is None

    def test_evolucao_item_com_variacao(self):
        now = datetime.now(timezone.utc)
        v = VariacaoScore(anterior=60.0, atual=75.0, diferenca=15.0, percentual=25.0, estavel=False)
        item = EvolucaoAvaliacaoItem(
            avaliacao_id=UUID(int=20),
            evaluated_at=now,
            score_alinhamento=75.0,
            score_potencial=65.0,
            classificacao_farol=ClassificacaoFarol.PRIORIDADE_MAXIMA,
            variacao_alinhamento=v,
            variacao_potencial=v,
        )
        assert item.variacao_alinhamento is not None
        assert item.variacao_alinhamento.diferenca == 15.0

    def test_evolucao_response_valida(self):
        now = datetime.now(timezone.utc)
        item = EvolucaoAvaliacaoItem(
            avaliacao_id=UUID(int=10),
            evaluated_at=now,
            score_alinhamento=75.0,
            score_potencial=65.0,
            classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
        )
        response = EvolucaoAvaliacaoResponse(
            checkpoint_id=UUID(int=1),
            items=[item],
            total=1,
        )
        assert response.total == 1
        assert response.items[0].score_alinhamento == 75.0
