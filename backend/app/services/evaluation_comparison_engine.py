from uuid import UUID

from app.schemas.comparacao import (
    ComparacaoAvaliacaoResponse,
    EvolucaoAvaliacaoItem,
    EvolucaoAvaliacaoResponse,
    VariacaoCriterio,
    VariacaoScore,
)


class EvaluationComparisonEngine:
    PESOS_ALINHAMENTO: dict[str, int] = {
        "tom_de_voz_azul": 25,
        "identidade_visual_azul": 20,
        "posicionamento_malha_regional": 20,
        "uso_correto_produtos_marca": 15,
        "seguranca_solidez": 10,
        "clareza_passageiro": 10,
    }

    PESOS_POTENCIAL: dict[str, int] = {
        "pilares_estrategicos_atuais": 25,
        "receita_produtos_proprios": 20,
        "alcance_malha_regional": 15,
        "diferenciacao_gol_latam": 15,
        "recuperacao_fidelizacao_cliente": 15,
        "viabilidade_operacional": 10,
    }

    @classmethod
    def _calcular_score(cls, criterios: dict, pesos: dict[str, int]) -> float:
        soma = 0.0
        for nome, peso in pesos.items():
            nota = criterios.get(nome, {}).get("nota", 0)
            soma += nota * peso / 100.0
        return round(soma, 2)

    @staticmethod
    def _compute_variacao_score(anterior: float, atual: float) -> VariacaoScore:
        diferenca = round(atual - anterior, 2)
        if anterior == 0:
            percentual = None
        else:
            percentual = round(((atual - anterior) / anterior) * 100, 2)
        estavel = abs(diferenca) < 0.01
        return VariacaoScore(
            anterior=anterior,
            atual=atual,
            diferenca=diferenca,
            percentual=percentual,
            estavel=estavel,
        )

    @staticmethod
    def _compute_variacao_criterio(
        nome: str, peso: int, anterior_nota: float, atual_nota: float
    ) -> VariacaoCriterio:
        diferenca = round(atual_nota - anterior_nota, 2)
        if anterior_nota == 0:
            percentual = None
        else:
            percentual = round(((atual_nota - anterior_nota) / anterior_nota) * 100, 2)
        estavel = abs(diferenca) < 0.01
        return VariacaoCriterio(
            nome=nome,
            peso=peso,
            anterior_nota=anterior_nota,
            atual_nota=atual_nota,
            diferenca=diferenca,
            percentual=percentual,
            estavel=estavel,
        )

    @classmethod
    def comparar(
        cls,
        anterior_id: UUID,
        atual_id: UUID,
        checkpoint_id: UUID,
        criterios_alinhamento_anterior: dict,
        criterios_potencial_anterior: dict,
        criterios_alinhamento_atual: dict,
        criterios_potencial_atual: dict,
    ) -> ComparacaoAvaliacaoResponse:
        score_alinhamento_anterior = cls._calcular_score(
            criterios_alinhamento_anterior, cls.PESOS_ALINHAMENTO
        )
        score_potencial_anterior = cls._calcular_score(
            criterios_potencial_anterior, cls.PESOS_POTENCIAL
        )
        score_alinhamento_atual = cls._calcular_score(
            criterios_alinhamento_atual, cls.PESOS_ALINHAMENTO
        )
        score_potencial_atual = cls._calcular_score(
            criterios_potencial_atual, cls.PESOS_POTENCIAL
        )

        variacao_alinhamento = cls._compute_variacao_score(
            score_alinhamento_anterior, score_alinhamento_atual
        )
        variacao_potencial = cls._compute_variacao_score(
            score_potencial_anterior, score_potencial_atual
        )

        criterios_alinhamento_variacao: list[VariacaoCriterio] = []
        for nome, peso in cls.PESOS_ALINHAMENTO.items():
            anterior_nota = criterios_alinhamento_anterior.get(nome, {}).get("nota", 0)
            atual_nota = criterios_alinhamento_atual.get(nome, {}).get("nota", 0)
            criterios_alinhamento_variacao.append(
                cls._compute_variacao_criterio(nome, peso, anterior_nota, atual_nota)
            )

        criterios_potencial_variacao: list[VariacaoCriterio] = []
        for nome, peso in cls.PESOS_POTENCIAL.items():
            anterior_nota = criterios_potencial_anterior.get(nome, {}).get("nota", 0)
            atual_nota = criterios_potencial_atual.get(nome, {}).get("nota", 0)
            criterios_potencial_variacao.append(
                cls._compute_variacao_criterio(nome, peso, anterior_nota, atual_nota)
            )

        todos_criterios = criterios_alinhamento_variacao + criterios_potencial_variacao

        nao_estaveis = [c for c in todos_criterios if not c.estavel]
        nao_estaveis.sort(key=lambda c: c.diferenca, reverse=True)

        maiores_melhorias = [c for c in nao_estaveis if c.diferenca > 0][:3]
        maiores_quedas = [c for c in nao_estaveis if c.diferenca < 0][:3]

        return ComparacaoAvaliacaoResponse(
            avaliacao_anterior_id=anterior_id,
            avaliacao_atual_id=atual_id,
            checkpoint_id=checkpoint_id,
            score_alinhamento=variacao_alinhamento,
            score_potencial=variacao_potencial,
            criterios_alinhamento=criterios_alinhamento_variacao,
            criterios_potencial=criterios_potencial_variacao,
            maiores_melhorias=maiores_melhorias,
            maiores_quedas=maiores_quedas,
        )

    @classmethod
    def resumo_evolucao(
        cls,
        checkpoint_id: UUID,
        historico: list[dict],
    ) -> EvolucaoAvaliacaoResponse:
        items: list[EvolucaoAvaliacaoItem] = []
        for i, item in enumerate(historico):
            variacao_alinhamento = None
            variacao_potencial = None
            if i > 0:
                prev = historico[i - 1]
                variacao_alinhamento = cls._compute_variacao_score(
                    prev["score_alinhamento"], item["score_alinhamento"]
                )
                variacao_potencial = cls._compute_variacao_score(
                    prev["score_potencial"], item["score_potencial"]
                )

            items.append(
                EvolucaoAvaliacaoItem(
                    avaliacao_id=item["avaliacao_id"],
                    evaluated_at=item["evaluated_at"],
                    score_alinhamento=item["score_alinhamento"],
                    score_potencial=item["score_potencial"],
                    classificacao_farol=item["classificacao_farol"],
                    variacao_alinhamento=variacao_alinhamento,
                    variacao_potencial=variacao_potencial,
                )
            )

        return EvolucaoAvaliacaoResponse(
            checkpoint_id=checkpoint_id,
            items=items,
            total=len(items),
        )
