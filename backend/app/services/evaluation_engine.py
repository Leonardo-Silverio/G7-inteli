from typing import ClassVar

from app.schemas.avaliacao import (
    AvaliacaoCalculada,
    AvaliacaoIAOutput,
    ClassificacaoFarol,
    ContribuicaoCriterio,
    CriterioAvaliacao,
    CriteriosAlinhamento,
    CriteriosPotencial,
)


class EvaluationEngine:
    PESOS_ALINHAMENTO: ClassVar[dict[str, int]] = {
        "tom_de_voz_azul": 25,
        "identidade_visual_azul": 20,
        "posicionamento_malha_regional": 20,
        "uso_correto_produtos_marca": 15,
        "seguranca_solidez": 10,
        "clareza_passageiro": 10,
    }

    PESOS_POTENCIAL: ClassVar[dict[str, int]] = {
        "pilares_estrategicos_atuais": 25,
        "receita_produtos_proprios": 20,
        "alcance_malha_regional": 15,
        "diferenciacao_gol_latam": 15,
        "recuperacao_fidelizacao_cliente": 15,
        "viabilidade_operacional": 10,
    }

    @classmethod
    def _validate_pesos(cls, pesos: dict[str, int]) -> None:
        total = sum(pesos.values())
        if total != 100:
            raise ValueError(f"Soma dos pesos deve ser 100, obtido: {total}")

    @classmethod
    def _validate_pesos_constantes(cls) -> None:
        cls._validate_pesos(cls.PESOS_ALINHAMENTO)
        cls._validate_pesos(cls.PESOS_POTENCIAL)

    @staticmethod
    def _iterar_criterios(criterios_model):
        return [(name, getattr(criterios_model, name)) for name in criterios_model.model_fields]

    @classmethod
    def _validar_criterio(cls, nome: str, criterio: CriterioAvaliacao) -> None:
        if criterio.feedback is None or not criterio.feedback.strip():
            raise ValueError(f"Feedback vazio para criterio: {nome}")
        if criterio.confianca is not None and (criterio.confianca < 0 or criterio.confianca > 100):
            raise ValueError(f"Confianca invalida para criterio {nome}: {criterio.confianca}")

    @staticmethod
    def _calcular_contribuicoes(
        criterios_model,
        pesos: dict[str, int],
    ) -> tuple[float, list[ContribuicaoCriterio]]:
        soma = 0.0
        contribuicoes: list[ContribuicaoCriterio] = []
        for nome, peso in pesos.items():
            criterio = getattr(criterios_model, nome)
            contribuicao = criterio.nota * peso / 100.0
            soma += contribuicao
            contribuicoes.append(
                ContribuicaoCriterio(
                    nome=nome,
                    nota=criterio.nota,
                    peso=peso,
                    contribuicao=round(contribuicao, 2),
                )
            )
        return round(soma, 2), contribuicoes

    @classmethod
    def calculate_alignment(cls, criteria: CriteriosAlinhamento) -> float:
        cls._validate_pesos_constantes()
        score, _ = cls._calcular_contribuicoes(criteria, cls.PESOS_ALINHAMENTO)
        return score

    @classmethod
    def calculate_potential(cls, criteria: CriteriosPotencial) -> float:
        cls._validate_pesos_constantes()
        score, _ = cls._calcular_contribuicoes(criteria, cls.PESOS_POTENCIAL)
        return score

    @staticmethod
    def classify(alignment_score: float, potential_score: float) -> str:
        if potential_score < 60:
            return "BAIXA_PRIORIDADE"
        if alignment_score < 70:
            return "VALE_INVESTIR_TEMPO"
        return "PRIORIDADE_MAXIMA"

    @classmethod
    def evaluate(cls, output: AvaliacaoIAOutput) -> AvaliacaoCalculada:
        cls._validate_pesos_constantes()

        criterios_alinhamento = output.criterios_alinhamento
        criterios_potencial = output.criterios_potencial

        for nome, criterio in criterios_alinhamento:
            cls._validar_criterio(nome, criterio)
        for nome, criterio in criterios_potencial:
            cls._validar_criterio(nome, criterio)

        score_alinhamento, contribuicoes_alinhamento = cls._calcular_contribuicoes(
            criterios_alinhamento, cls.PESOS_ALINHAMENTO
        )
        score_potencial, contribuicoes_potencial = cls._calcular_contribuicoes(
            criterios_potencial, cls.PESOS_POTENCIAL
        )

        classificacao = cls.classify(score_alinhamento, score_potencial)

        return AvaliacaoCalculada(
            score_alinhamento=score_alinhamento,
            score_potencial=score_potencial,
            classificacao_farol=classificacao,
            criterios_alinhamento=criterios_alinhamento,
            criterios_potencial=criterios_potencial,
            feedback_geral=output.feedback_geral,
            resumo_para_marketing=output.resumo_para_marketing,
            contribuicoes_alinhamento=contribuicoes_alinhamento,
            contribuicoes_potencial=contribuicoes_potencial,
        )