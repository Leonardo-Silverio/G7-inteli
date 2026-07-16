import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import TipoCheckpoint
from app.schemas.checkpoint import (
    IdeacaoFormData,
    DesenvolvimentoFormData,
    PreLancamentoFormData,
)
from app.schemas.avaliacao import AvaliacaoIAOutput


@dataclass
class CheckpointEvaluationContext:
    checkpoint_id: UUID
    projeto_id: UUID
    tipo_checkpoint: TipoCheckpoint
    versao_formulario: str
    versao_business: str
    schema_version: int
    respostas: dict[str, Any]
    anexos: list[dict[str, Any]]
    avaliacoes_anteriores: list[dict[str, Any]] | None = None
    conversa_resumida: str | None = None

    def to_prompt_context(self) -> str:
        parts = [
            f"CHECKPOINT: {self.tipo_checkpoint.value}",
            f"VERSÃO FORMULÁRIO: {self.versao_formulario}",
            f"VERSÃO BUSINESS: {self.versao_business}",
            f"SCHEMA VERSION: {self.schema_version}",
            "",
            "RESPOSTAS DO FORMULÁRIO:",
            json.dumps(self.respostas, ensure_ascii=False, indent=2),
        ]
        if self.anexos:
            parts.append("")
            parts.append("ANEXOS (metadados):")
            parts.append(json.dumps(self.anexos, ensure_ascii=False, indent=2))
        if self.avaliacoes_anteriores:
            parts.append("")
            parts.append("AVALIAÇÕES ANTERIORES:")
            parts.append(json.dumps(self.avaliacoes_anteriores, ensure_ascii=False, indent=2))
        if self.conversa_resumida:
            parts.append("")
            parts.append("RESUMO DA CONVERSA (controlado):")
            parts.append(self.conversa_resumida)
        return "\n".join(parts)


SYSTEM_PROMPT_BASE = """Você é um avaliador especializado da Azul Linhas Aéreas para o programa Farol.
Sua função é analisar checkpoints de projetos e fornecer notas detalhadas por critério.

REGRAS OBRIGATÓRIAS:
1. Retorne APENAS JSON válido compatível com o schema fornecido.
2. NÃO inclua score_alinhamento, score_potencial ou classificacao_farol no JSON.
3. NÃO calcule pesos ou scores finais.
4. Para cada critério, forneça: nota (0-100), feedback (string não vazia), evidencias (array), sugestoes (array), confianca (0-100 opcional).
5. Feedback deve ser específico e acionável.
6. Evidencias devem citar trechos das respostas do formulário.
7. feedback_geral e resumo_para_marketing são obrigatórios.
8. NÃO use markdown, comentários ou texto extra.
9. O resumo_para_marketing deve ser adequado para a área de Marketing: sem dados sensíveis, sem conversa bruta, sem invenções.
10. Regras de privacidade: não exponha dados pessoais, não reproduza conversa bruta, não invente fatos."""


CRITERIOS_ALINHAMENTO = {
    "tom_de_voz_azul": {
        "peso": 25,
        "descricao": "Comunicação alinhada ao tom de voz da marca Azul: próxima, acolhedora, confiável, humana.",
        "guia": "Avalie se a linguagem reflete proximidade com o cliente, uso de 'você', tom empático, clareza e identidade verbal da Azul.",
    },
    "identidade_visual_azul": {
        "peso": 20,
        "descricao": "Uso correto da identidade visual: cores, logo, tipografia, iconografia, padrões da marca.",
        "guia": "Verifique aderência ao brand guide: Azul 001, Azul 002, Branco, Cinza. Uso correto do logotipo e elementos gráficos.",
    },
    "posicionamento_malha_regional": {
        "peso": 20,
        "descricao": "Posicionamento que valoriza a malha regional da Azul como diferencial competitivo.",
        "guia": "O projeto destaca capilaridade, destinos exclusivos, conectividade regional? Há menção a rotas regionais como ativo?",
    },
    "uso_correto_produtos_marca": {
        "peso": 15,
        "descricao": "Referência correta aos produtos próprios: Azul Fidelidade, Azul Viagens, Azul Cargo, Azul Empresas.",
        "guia": "Nomes corretos, contexto apropriado, sinergia entre produtos demonstrada.",
    },
    "seguranca_solidez": {
        "peso": 10,
        "descricao": "Transmissão de segurança, solidez operacional e confiança na marca.",
        "guia": "Linguagem que passa confiabilidade, menção a certificações, histórico de segurança, solidez financeira.",
    },
    "clareza_passageiro": {
        "peso": 10,
        "descricao": "Clareza na comunicação para o passageiro final: entendimento imediato, sem jargões desnecessários.",
        "guia": "Informação acessível, estrutura lógica, chamadas claras, CTA óbvio.",
    },
}

CRITERIOS_POTENCIAL = {
    "pilares_estrategicos_atuais": {
        "peso": 25,
        "descricao": "Alinhamento aos pilares estratégicos atuais da Azul: Reconquista de Cliente, Fortalecimento da Malha Regional, Diversificação de Receita, Disciplina Financeira.",
        "guia": "O projeto ataca diretamente um ou mais pilares? Há conexão explícita com a estratégia corporativa?",
    },
    "receita_produtos_proprios": {
        "peso": 20,
        "descricao": "Potencial de gerar receita através de produtos próprios da Azul (Fidelidade, Viagens, Cargo, Empresas).",
        "guia": "Projeção de receita incremental, cross-sell, up-sell, uso da base de clientes.",
    },
    "alcance_malha_regional": {
        "peso": 15,
        "descricao": "Capilaridade e alcance da malha regional como vetor de crescimento.",
        "guia": "Projeto expande cobertura? Conecta destinos subatendidos? Aproveita slots regionais?",
    },
    "diferenciacao_gol_latam": {
        "peso": 15,
        "descricao": "Diferenciação clara frente a GOL e LATAM: proposta única, não replicável facilmente.",
        "guia": "O que só a Azul pode fazer? Malha regional, cultura de serviço, ecossistema de produtos próprios.",
    },
    "recuperacao_fidelizacao_cliente": {
        "peso": 15,
        "descricao": "Contribuição para recuperar e fidelizar clientes: experiência, benefícios, engajamento.",
        "guia": "Mecânicas de retenção, NPS, frequência, share of wallet, resgate de inativos.",
    },
    "viabilidade_operacional": {
        "peso": 10,
        "descricao": "Viabilidade técnica, operacional, regulatória e de recursos para execução.",
        "guia": "Recursos necessários, dependências, riscos de execução, compliance, timeline realista.",
    },
}


def _format_criterios_prompt(criterios: dict) -> str:
    lines = []
    for nome, info in criterios.items():
        lines.append(f"- {nome} (peso {info['peso']}%): {info['descricao']}")
        lines.append(f"  Guia: {info['guia']}")
    return "\n".join(lines)


def _get_checkpoint_specific_prompt(tipo: TipoCheckpoint) -> str:
    prompts = {
        TipoCheckpoint.IDEACAO: """CHECKPOINT 1 — IDEAÇÃO
Pergunta central: "Essa ideia está madura o suficiente para virar um projeto?"

Foque sua análise em:
- Problema/oportunidade: clareza, relevância, tamanho do prêmio
- Proposta da solução: viabilidade, inovação, aderência à Azul
- Foco estratégico: conexão com pilares (Reconquista, Malha Regional, Diversificação, Disciplina)
- Impacto regional: potencial de fortalecer a malha regional
- Possível duplicação: projetos similares existentes, sinergias ou conflitos
- Prazo: realismo do time-to-market
- Dependências: riscos de bloqueio, dependências críticas
- Diferenciação: o que torna único vs. concorrentes e interno
- Informações adicionais: dados não compartilhados, riscos ocultos""",
        TipoCheckpoint.DESENVOLVIMENTO: """CHECKPOINT 2 — DESENVOLVIMENTO
Pergunta central: "Essa ideia foi transformada em uma execução bem desenvolvida?"

Foque sua análise em:
- Material desenvolvido: qualidade, completude, aderência ao briefing
- Produtos e marcas envolvidos: uso correto de Azul Fidelidade, Viagens, Cargo, Empresas
- Tom de comunicação: escala 1-5 (Muito Próximo a Muito Formal), adequação ao público
- Mudanças desde Ideaçao: evolução positiva, pivôs justificados
- Aplicação do feedback anterior: endereçamento de pontos da Ideaçao
- Limitações internas: transparência sobre restrições, planos de mitigação""",
        TipoCheckpoint.PRE_LANCAMENTO: """CHECKPOINT 3 — PRÉ-LANÇAMENTO
Pergunta central: "Esse projeto está pronto para representar a Azul no mercado?"

Foque sua análise em:
- Material final: qualidade de lançamento, aprovações internas
- Áreas envolvidas: alinhamento entre Marketing, Operações, Jurídico, TI, Comercial
- Dados de clientes: conformidade LGPD, consentimento, uso ético
- Revisão jurídica/compliance: aprovações formais, riscos mapeados
- Confirmação de tarifas/benefícios/condições: precisão comercial
- Risco de má interpretação: clareza nas comunicações, FAQ preparado
- Conflito com campanhas: calendário, mensagens sobrepostas, canibalização
- Data prevista: realismo, dependências de go-live
- Riscos finais: plano de contingência, monitoramento pós-lançamento""",
    }
    return prompts.get(tipo, "")


def build_prompt(context: CheckpointEvaluationContext) -> tuple[str, str]:
    system_prompt = SYSTEM_PROMPT_BASE + "\n\n" + _format_criteria_for_prompt()

    user_prompt = f"""{_get_checkpoint_specific_prompt(context.tipo_checkpoint)}

{context.to_prompt_context()}

Retorne JSON com a estrutura exata:
{{
  "criterios_alinhamento": {{...}},
  "criterios_potencial": {{...}},
  "feedback_geral": "...",
  "resumo_para_marketing": "..."
}}

Cada critério deve ter: nota, feedback, evidencias, sugestoes, confianca (opcional)."""

    return system_prompt, user_prompt


def _format_criteria_for_prompt() -> str:
    lines = ["CRITÉRIOS DE ALINHAMENTO (pesos somam 100%):"]
    lines.append(_format_criterios_prompt(CRITERIOS_ALINHAMENTO))
    lines.append("\nCRITÉRIOS DE POTENCIAL (pesos somam 100%):")
    lines.append(_format_criterios_prompt(CRITERIOS_POTENCIAL))
    return "\n".join(lines)


def calculate_prompt_hash(system_prompt: str, user_prompt: str) -> str:
    combined = system_prompt + "|" + user_prompt
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def calculate_criteria_hash() -> str:
    criteria_data = {
        "alinhamento": CRITERIOS_ALINHAMENTO,
        "potencial": CRITERIOS_POTENCIAL,
    }
    serialized = json.dumps(criteria_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


PROMPT_VERSION = "checkpoint_v1"
CRITERIA_VERSION = "business_rules_2026_07"
EVALUATION_ENGINE = "farol-engine-v1"