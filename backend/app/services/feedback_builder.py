from app.schemas.avaliacao import (
    AvaliacaoCalculada,
    FeedbackItem,
    FeedbackEstruturado,
)


class FeedbackBuilder:
    @staticmethod
    def gerar_justificativa(calculada: AvaliacaoCalculada) -> str:
        score_a = calculada.score_alinhamento
        score_p = calculada.score_potencial
        classificacao = calculada.classificacao_farol

        contrib_a = sorted(
            calculada.contribuicoes_alinhamento,
            key=lambda c: c.contribuicao,
            reverse=True,
        )
        contrib_p = sorted(
            calculada.contribuicoes_potencial,
            key=lambda c: c.contribuicao,
            reverse=True,
        )

        top_a = contrib_a[0] if contrib_a else None
        top_p = contrib_p[0] if contrib_p else None
        bottom_a = contrib_a[-1] if len(contrib_a) > 1 else None
        bottom_p = contrib_p[-1] if len(contrib_p) > 1 else None

        partes: list[str] = []

        if classificacao == "PRIORIDADE_MAXIMA":
            partes.append(
                "Classificação: PRIORIDADE MÁXIMA"
            )
            partes.append(
                f"Score de Alinhamento {score_a:.1f} (mínimo 70) e "
                f"Score de Potencial {score_p:.1f} (mínimo 60) atendem aos critérios do Farol."
            )
        elif classificacao == "VALE_INVESTIR_TEMPO":
            partes.append("Classificação: VALE INVESTIR TEMPO")
            if score_a < 70:
                partes.append(
                    f"Score de Potencial {score_p:.1f} atende ao mínimo (≥60), "
                    f"mas Score de Alinhamento {score_a:.1f} está abaixo de 70. "
                    "O projeto tem mérito estratégico, mas precisa ajustar a comunicação com a marca."
                )
            else:
                partes.append(
                    f"Score de Alinhamento {score_a:.1f} e Score de Potencial {score_p:.1f} "
                    "se enquadram nas regras de classificação do Farol."
                )
        elif classificacao == "BAIXA_PRIORIDADE":
            partes.append("Classificação: BAIXA PRIORIDADE")
            partes.append(
                f"Score de Potencial {score_p:.1f} está abaixo do mínimo de 60. "
                "O projeto não atingiu o patamar necessário de contribuição estratégica."
            )

        if top_a and top_p:
            partes.append(
                f"Maior contribuição positiva: {top_a.nome} (Alinhamento, {top_a.nota:.1f}) "
                f"e {top_p.nome} (Potencial, {top_p.nota:.1f})."
            )
        if bottom_a:
            partes.append(
                f"Maior oportunidade de melhoria: {bottom_a.nome} (Alinhamento, {bottom_a.nota:.1f})."
            )
        if bottom_p:
            partes.append(
                f"Maior oportunidade de melhoria: {bottom_p.nome} (Potencial, {bottom_p.nota:.1f})."
            )

        return " ".join(partes)

    @staticmethod
    def montar_feedback_json(
        calculada: AvaliacaoCalculada,
        *,
        pontos_fortes: list[FeedbackItem] | None = None,
        oportunidades_melhoria: list[FeedbackItem] | None = None,
        recomendacoes_praticas: list[FeedbackItem] | None = None,
        proximos_passos: list[str] | None = None,
        riscos_principais: list[FeedbackItem] | None = None,
    ) -> dict:
        justificativa = FeedbackBuilder.gerar_justificativa(calculada)
        return FeedbackEstruturado(
            schema_version="feedback_v1",
            justificativa_classificacao=justificativa,
            pontos_fortes=pontos_fortes or [],
            oportunidades_melhoria=oportunidades_melhoria or [],
            recomendacoes_praticas=recomendacoes_praticas or [],
            proximos_passos=proximos_passos or [],
            riscos_principais=riscos_principais or [],
        ).model_dump()
