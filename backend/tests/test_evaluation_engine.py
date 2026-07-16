import pytest
from pydantic import ValidationError

from app.schemas.avaliacao import (
    AvaliacaoCalculada,
    AvaliacaoIAOutput,
    CriterioAvaliacao,
    CriteriosAlinhamento,
    CriteriosPotencial,
)
from app.services.evaluation_engine import EvaluationEngine


def _criterio_valido(nota: float = 100, feedback: str = "Ok", confianca: float | None = 90) -> CriterioAvaliacao:
    return CriterioAvaliacao(nota=nota, feedback=feedback, confianca=confianca)


def _alinhamento_todos(nota: float) -> CriteriosAlinhamento:
    c = _criterio_valido(nota)
    return CriteriosAlinhamento(
        tom_de_voz_azul=c,
        identidade_visual_azul=c,
        posicionamento_malha_regional=c,
        uso_correto_produtos_marca=c,
        seguranca_solidez=c,
        clareza_passageiro=c,
    )


def _potencial_todos(nota: float) -> CriteriosPotencial:
    c = _criterio_valido(nota)
    return CriteriosPotencial(
        pilares_estrategicos_atuais=c,
        receita_produtos_proprios=c,
        alcance_malha_regional=c,
        diferenciacao_gol_latam=c,
        recuperacao_fidelizacao_cliente=c,
        viabilidade_operacional=c,
    )


def _output_base(
    alinhamento: CriteriosAlinhamento | None = None,
    potencial: CriteriosPotencial | None = None,
) -> AvaliacaoIAOutput:
    return AvaliacaoIAOutput(
        criterios_alinhamento=alinhamento or _alinhamento_todos(100),
        criterios_potencial=potencial or _potencial_todos(100),
        feedback_geral="Feedback geral",
        resumo_para_marketing="Resumo marketing",
    )


class TestEvaluationEngine:
    def test_todos_100_alinhamento_100_potencial_100_prioridade_maxima(self):
        output = _output_base(_alinhamento_todos(100), _potencial_todos(100))
        result = EvaluationEngine.evaluate(output)
        assert result.score_alinhamento == 100.0
        assert result.score_potencial == 100.0
        assert result.classificacao_farol == "PRIORIDADE_MAXIMA"

    def test_todos_0_alinhamento_0_potencial_0_baixa_prioridade(self):
        output = _output_base(_alinhamento_todos(0), _potencial_todos(0))
        result = EvaluationEngine.evaluate(output)
        assert result.score_alinhamento == 0.0
        assert result.score_potencial == 0.0
        assert result.classificacao_farol == "BAIXA_PRIORIDADE"

    def test_potencial_59_99_baixa_prioridade_independente_alinhamento(self):
        output = _output_base(_alinhamento_todos(100), _potencial_todos(59.99))
        result = EvaluationEngine.evaluate(output)
        assert result.classificacao_farol == "BAIXA_PRIORIDADE"

    def test_potencial_60_alinhamento_69_99_vale_investir(self):
        output = _output_base(_alinhamento_todos(69.99), _potencial_todos(60))
        result = EvaluationEngine.evaluate(output)
        assert result.classificacao_farol == "VALE_INVESTIR_TEMPO"

    def test_potencial_60_alinhamento_70_prioridade_maxima(self):
        output = _output_base(_alinhamento_todos(70), _potencial_todos(60))
        result = EvaluationEngine.evaluate(output)
        assert result.classificacao_farol == "PRIORIDADE_MAXIMA"

    def test_calculo_ponderado_notas_diferentes(self):
        alinhamento = CriteriosAlinhamento(
            tom_de_voz_azul=_criterio_valido(80),
            identidade_visual_azul=_criterio_valido(90),
            posicionamento_malha_regional=_criterio_valido(70),
            uso_correto_produtos_marca=_criterio_valido(60),
            seguranca_solidez=_criterio_valido(50),
            clareza_passageiro=_criterio_valido(40),
        )
        potencial = CriteriosPotencial(
            pilares_estrategicos_atuais=_criterio_valido(90),
            receita_produtos_proprios=_criterio_valido(80),
            alcance_malha_regional=_criterio_valido(70),
            diferenciacao_gol_latam=_criterio_valido(60),
            recuperacao_fidelizacao_cliente=_criterio_valido(50),
            viabilidade_operacional=_criterio_valido(40),
        )
        output = _output_base(alinhamento, potencial)
        result = EvaluationEngine.evaluate(output)

        expected_alinhamento = round(
            80 * 0.25 + 90 * 0.20 + 70 * 0.20 + 60 * 0.15 + 50 * 0.10 + 40 * 0.10, 2
        )
        expected_potencial = round(
            90 * 0.25 + 80 * 0.20 + 70 * 0.15 + 60 * 0.15 + 50 * 0.15 + 40 * 0.10, 2
        )
        assert result.score_alinhamento == expected_alinhamento
        assert result.score_potencial == expected_potencial

    def test_resultado_arredondado_duas_casas(self):
        alinhamento = CriteriosAlinhamento(
            tom_de_voz_azul=_criterio_valido(33.333),
            identidade_visual_azul=_criterio_valido(33.333),
            posicionamento_malha_regional=_criterio_valido(33.334),
            uso_correto_produtos_marca=_criterio_valido(33.333),
            seguranca_solidez=_criterio_valido(33.333),
            clareza_passageiro=_criterio_valido(33.334),
        )
        potencial = _potencial_todos(33.333)
        output = _output_base(alinhamento, potencial)
        result = EvaluationEngine.evaluate(output)
        assert result.score_alinhamento == round(result.score_alinhamento, 2)
        assert result.score_potencial == round(result.score_potencial, 2)

    def test_nota_invalida_menor_que_zero(self):
        with pytest.raises(ValidationError):
            _criterio_valido(nota=-1)

    def test_nota_invalida_maior_que_100(self):
        with pytest.raises(ValidationError):
            _criterio_valido(nota=101)

    def test_feedback_vazio(self):
        with pytest.raises(ValidationError):
            _criterio_valido(feedback="")

    def test_campo_extra_rejeitado(self):
        with pytest.raises(ValidationError):
            CriterioAvaliacao(nota=50, feedback="Ok", extra_campo="valor")

    def test_criterio_obrigatorio_ausente(self):
        with pytest.raises(ValidationError):
            CriteriosAlinhamento(
                tom_de_voz_azul=_criterio_valido(),
                identidade_visual_azul=_criterio_valido(),
                posicionamento_malha_regional=_criterio_valido(),
                uso_correto_produtos_marca=_criterio_valido(),
                seguranca_solidez=_criterio_valido(),
            )

    def test_confianca_invalida(self):
        with pytest.raises(ValidationError):
            _criterio_valido(confianca=-1)
        with pytest.raises(ValidationError):
            _criterio_valido(confianca=101)

    def test_pesos_somam_100(self):
        assert sum(EvaluationEngine.PESOS_ALINHAMENTO.values()) == 100
        assert sum(EvaluationEngine.PESOS_POTENCIAL.values()) == 100

    def test_contribuicoes_incluidas_no_resultado(self):
        output = _output_base(_alinhamento_todos(80), _potencial_todos(70))
        result = EvaluationEngine.evaluate(output)
        assert len(result.contribuicoes_alinhamento) == 6
        assert len(result.contribuicoes_potencial) == 6
        for c in result.contribuicoes_alinhamento:
            assert c.nome in EvaluationEngine.PESOS_ALINHAMENTO
            assert c.peso == EvaluationEngine.PESOS_ALINHAMENTO[c.nome]
            assert c.contribuicao == round(c.nota * c.peso / 100, 2)

    def test_classificacao_limites_exatos(self):
        assert EvaluationEngine.classify(69.99, 60) == "VALE_INVESTIR_TEMPO"
        assert EvaluationEngine.classify(70, 60) == "PRIORIDADE_MAXIMA"
        assert EvaluationEngine.classify(100, 59.99) == "BAIXA_PRIORIDADE"
        assert EvaluationEngine.classify(100, 60) == "PRIORIDADE_MAXIMA"
        assert EvaluationEngine.classify(0, 60) == "VALE_INVESTIR_TEMPO"

    def test_engine_pura_deterministica(self):
        output = _output_base(_alinhamento_todos(75.5), _potencial_todos(65.5))
        r1 = EvaluationEngine.evaluate(output)
        r2 = EvaluationEngine.evaluate(output)
        assert r1.score_alinhamento == r2.score_alinhamento
        assert r1.score_potencial == r2.score_potencial
        assert r1.classificacao_farol == r2.classificacao_farol

    def test_avaliacao_calculada_contem_todos_campos(self):
        output = _output_base(_alinhamento_todos(80), _potencial_todos(70))
        result = EvaluationEngine.evaluate(output)
        assert isinstance(result, AvaliacaoCalculada)
        assert hasattr(result, "score_alinhamento")
        assert hasattr(result, "score_potencial")
        assert hasattr(result, "classificacao_farol")
        assert hasattr(result, "criterios_alinhamento")
        assert hasattr(result, "criterios_potencial")
        assert hasattr(result, "feedback_geral")
        assert hasattr(result, "resumo_para_marketing")
        assert hasattr(result, "contribuicoes_alinhamento")
        assert hasattr(result, "contribuicoes_potencial")


class TestSchemas:
    def test_criterio_avaliacao_valido(self):
        c = CriterioAvaliacao(nota=85, feedback="Bom", evidencias=["e1"], sugestoes=["s1"], confianca=90)
        assert c.nota == 85
        assert c.feedback == "Bom"
        assert c.evidencias == ["e1"]
        assert c.sugestoes == ["s1"]
        assert c.confianca == 90

    def test_criterio_avaliacao_strip_whitespace(self):
        c = CriterioAvaliacao(nota=50, feedback="  Bom  ", evidencias=["  e1  "], sugestoes=["  s1  "])
        assert c.feedback == "Bom"
        assert c.evidencias == ["e1"]
        assert c.sugestoes == ["s1"]

    def test_avaliacao_ia_output_nao_aceita_score_alinhamento(self):
        with pytest.raises(ValidationError):
            AvaliacaoIAOutput(
                criterios_alinhamento=_alinhamento_todos(100),
                criterios_potencial=_potencial_todos(100),
                feedback_geral="f",
                resumo_para_marketing="r",
                score_alinhamento=100,
            )

    def test_avaliacao_ia_output_nao_aceita_score_potencial(self):
        with pytest.raises(ValidationError):
            AvaliacaoIAOutput(
                criterios_alinhamento=_alinhamento_todos(100),
                criterios_potencial=_potencial_todos(100),
                feedback_geral="f",
                resumo_para_marketing="r",
                score_potencial=100,
            )

    def test_avaliacao_ia_output_nao_aceita_classificacao(self):
        with pytest.raises(ValidationError):
            AvaliacaoIAOutput(
                criterios_alinhamento=_alinhamento_todos(100),
                criterios_potencial=_potencial_todos(100),
                feedback_geral="f",
                resumo_para_marketing="r",
                classificacao_farol="PRIORIDADE_MAXIMA",
            )

    def test_pesos_alinhamento_nomes_exatos(self):
        expected = {
            "tom_de_voz_azul",
            "identidade_visual_azul",
            "posicionamento_malha_regional",
            "uso_correto_produtos_marca",
            "seguranca_solidez",
            "clareza_passageiro",
        }
        assert set(EvaluationEngine.PESOS_ALINHAMENTO.keys()) == expected

    def test_pesos_potencial_nomes_exatos(self):
        expected = {
            "pilares_estrategicos_atuais",
            "receita_produtos_proprios",
            "alcance_malha_regional",
            "diferenciacao_gol_latam",
            "recuperacao_fidelizacao_cliente",
            "viabilidade_operacional",
        }
        assert set(EvaluationEngine.PESOS_POTENCIAL.keys()) == expected