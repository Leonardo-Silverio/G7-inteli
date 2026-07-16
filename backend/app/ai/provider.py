from typing import Any, Protocol
from dataclasses import dataclass
from app.config.settings import settings


class AIProvider(Protocol):
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        ...


class AIProviderError(Exception):
    pass


class AIInvalidResponseError(AIProviderError):
    pass


class AIResponseValidationError(AIProviderError):
    pass


@dataclass
class ProviderConfig:
    api_key: str | None = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 60


class OpenAIProvider:
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig(
            api_key=getattr(settings, "OPENAI_API_KEY", None),
            model="gpt-4o-mini",
        )
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.config.api_key:
                raise AIProviderError("API key não configurada")
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )
        return self._client

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise AIInvalidResponseError("Resposta vazia da IA")
            import json
            return json.loads(content)
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(f"Erro ao chamar provedor de IA: {type(e).__name__}")


class FakeAIProvider:
    def __init__(self, response: dict[str, Any] | None = None, should_fail: bool = False):
        self._response = response or {}
        self._should_fail = should_fail
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        if self._should_fail:
            raise AIProviderError("Erro simulado do provedor")
        return self._response