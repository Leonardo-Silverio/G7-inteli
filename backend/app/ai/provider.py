import json
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
    model: str = "deepseek-v4-flash"
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 30


class DeepSeekProvider:
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL,
            timeout=30,
        )
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.config.api_key:
                raise AIProviderError("API key DeepSeek não configurada")
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url="https://api.deepseek.com/v1",
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
                stream=False,
            )
            content = response.choices[0].message.content
            if not content:
                raise AIInvalidResponseError("Resposta vazia da IA")
            return self._parse_json(content)
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(f"Erro ao chamar DeepSeek: {type(e).__name__}")

    def _parse_json(self, content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
            content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise AIInvalidResponseError("Resposta da IA não é um JSON válido")


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


def get_ai_provider() -> AIProvider:
    if settings.DEEPSEEK_API_KEY:
        return DeepSeekProvider()
    return FakeAIProvider()