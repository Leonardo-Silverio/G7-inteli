from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.ai.provider import AIProvider, AIProviderError, AIInvalidResponseError, AIResponseValidationError
from app.ai.checkpoint_prompt import (
    build_prompt,
    calculate_prompt_hash,
    calculate_criteria_hash,
    PROMPT_VERSION,
    CRITERIA_VERSION,
    EVALUATION_ENGINE,
    CheckpointEvaluationContext,
)
from app.schemas.avaliacao import AvaliacaoIAOutput


@dataclass
class EvaluationMetadata:
    evaluation_engine: str
    modelo: str
    prompt_version: str
    criteria_version: str
    prompt_hash: str
    criteria_hash: str


class CheckpointAIEvaluator:
    def __init__(
        self,
        provider: AIProvider,
        *,
        modelo: str = "gpt-4o-mini",
        prompt_version: str = PROMPT_VERSION,
        criteria_version: str = CRITERIA_VERSION,
    ):
        self.provider = provider
        self.modelo = modelo
        self.prompt_version = prompt_version
        self.criteria_version = criteria_version

    def evaluate(self, context: CheckpointEvaluationContext) -> tuple[AvaliacaoIAOutput, EvaluationMetadata]:
        system_prompt, user_prompt = build_prompt(context)

        try:
            raw_response = self.provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(f"Erro inesperado ao chamar provedor: {type(e).__name__}")

        if not isinstance(raw_response, dict):
            raise AIInvalidResponseError("Resposta da IA não é um objeto JSON")

        try:
            avaliacao = AvaliacaoIAOutput.model_validate(raw_response)
        except Exception as e:
            raise AIResponseValidationError(f"Resposta da IA não conforma ao schema: {type(e).__name__}")

        prompt_hash = calculate_prompt_hash(system_prompt, user_prompt)
        criteria_hash = calculate_criteria_hash()

        metadata = EvaluationMetadata(
            evaluation_engine=EVALUATION_ENGINE,
            modelo=self.modelo,
            prompt_version=self.prompt_version,
            criteria_version=self.criteria_version,
            prompt_hash=prompt_hash,
            criteria_hash=criteria_hash,
        )

        return avaliacao, metadata