"""Endpoints com dados ficticios para a demonstracao do Farol."""

from datetime import UTC, datetime
from time import sleep

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/demo", tags=["Demonstração"])


class EvaluationRequest(BaseModel):
    project_id: int
    description: str = Field(min_length=3, max_length=2000)


PROJECTS = [
    {
        "id": 1,
        "name": "Roteiros Inteligentes",
        "vertical": "Viagens",
        "owner": "Marina Costa",
        "stage": "Desenvolvimento",
        "status": "attention",
        "score": 68,
        "updated": "Hoje, 10:42",
    },
    {
        "id": 2,
        "name": "Clube de Benefícios",
        "vertical": "Conecta",
        "owner": "Rafael Lima",
        "stage": "Pré-lançamento",
        "status": "approved",
        "score": 91,
        "updated": "Ontem, 16:20",
    },
    {
        "id": 3,
        "name": "Carteira Verde",
        "vertical": "Financeiro",
        "owner": "Ana Souza",
        "stage": "Ideação",
        "status": "risk",
        "score": 42,
        "updated": "15 jul, 14:10",
    },
]


@router.get("/dashboard")
def dashboard():
    return {
        "summary": {"active": 12, "approved": 7, "attention": 3, "risk": 2},
        "projects": PROJECTS,
        "mode": "simulation",
    }


@router.post("/evaluate")
def evaluate(payload: EvaluationRequest):
    # Pequena pausa deixa a interacao convincente sem chamar qualquer IA externa.
    sleep(0.8)
    return {
        "project_id": payload.project_id,
        "score": 76,
        "classification": "attention",
        "title": "Bom potencial, com pontos para validar",
        "summary": (
            "A proposta está alinhada à estratégia da vertical e apresenta valor claro "
            "para o cliente. Antes do próximo checkpoint, valide as métricas de sucesso "
            "e detalhe o plano de adoção."
        ),
        "strengths": [
            "Problema do cliente bem definido",
            "Boa aderência aos objetivos da vertical",
            "Escopo viável para um primeiro lançamento",
        ],
        "alerts": [
            "Métrica de sucesso ainda não possui uma meta numérica",
            "Plano de comunicação precisa de um responsável",
        ],
        "next_step": "Definir uma meta de conversão e validar o plano com Marketing.",
        "generated_at": datetime.now(UTC).isoformat(),
        "simulated": True,
    }
