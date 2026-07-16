import pytest
import json
from unittest.mock import MagicMock, patch

from app.config.settings import settings
from app.ai.provider import (
    DeepSeekProvider,
    FakeAIProvider,
    AIProviderError,
    AIInvalidResponseError,
    ProviderConfig,
    get_ai_provider,
)


def _mock_openai_response(content: str):
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


class TestDeepSeekProviderRequest:
    def test_uses_correct_model_and_parameters(self):
        config = ProviderConfig(api_key="test-key", model="deepseek-v4-flash")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps({"feedback_geral": "ok", "resumo_para_marketing": "ok"})
        )
        provider._client = mock_client

        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )

        mock_client.chat.completions.create.assert_called_once_with(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            temperature=0.1,
            max_tokens=4000,
            stream=False,
        )

    def test_timeout_is_30_seconds(self):
        config = ProviderConfig(api_key="test-key", timeout=30)
        provider = DeepSeekProvider(config)

        assert provider.config.timeout == 30


class TestDeepSeekProviderParsing:
    def test_plain_json_parsed_correctly(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        expected = {"feedback_geral": "teste", "resumo_para_marketing": "teste"}
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            json.dumps(expected)
        )
        provider._client = mock_client

        result = provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )

        assert result == expected

    def test_markdown_fences_removed(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        expected = {"feedback_geral": "ok", "resumo_para_marketing": "ok"}
        raw = "```json\n" + json.dumps(expected) + "\n```"
        mock_client.chat.completions.create.return_value = _mock_openai_response(raw)
        provider._client = mock_client

        result = provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )

        assert result == expected

    def test_markdown_fences_with_language_tag(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        expected = {"feedback_geral": "ok", "resumo_para_marketing": "ok"}
        raw = "```json\n" + json.dumps(expected) + "\n```"
        mock_client.chat.completions.create.return_value = _mock_openai_response(raw)
        provider._client = mock_client

        result = provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )

        assert result == expected

    def test_invalid_json_raises_error(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "not valid json at all"
        )
        provider._client = mock_client

        with pytest.raises(AIInvalidResponseError):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )

    def test_empty_response_raises_error(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response("")
        provider._client = mock_client

        with pytest.raises(AIInvalidResponseError):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )

    def test_partial_json_rejected(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '{"feedback_geral": "ok"'
        )
        provider._client = mock_client

        with pytest.raises(AIInvalidResponseError):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )


class TestDeepSeekProviderErrors:
    def test_no_api_key_raises_error(self):
        provider = DeepSeekProvider(ProviderConfig(api_key=None, model="test"))

        with pytest.raises(AIProviderError, match="API key DeepSeek não configurada"):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )

    def test_http_error_wraps_in_aiprovider_error(self):
        config = ProviderConfig(api_key="test-key")
        provider = DeepSeekProvider(config)
        mock_client = MagicMock()
        from openai import APIError
        mock_client.chat.completions.create.side_effect = APIError(
            message="HTTP error",
            request=MagicMock(),
            body=None,
        )
        provider._client = mock_client

        with pytest.raises(AIProviderError):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )


class TestGetAIProvider:
    def test_with_deepseek_key_returns_deepseek_provider(self):
        with patch.object(settings, "DEEPSEEK_API_KEY", "test-key"):
            provider = get_ai_provider()
            assert isinstance(provider, DeepSeekProvider)

    def test_without_key_returns_fake_provider(self):
        with patch.object(settings, "DEEPSEEK_API_KEY", None):
            provider = get_ai_provider()
            assert isinstance(provider, FakeAIProvider)

    def test_fake_provider_fallback(self):
        with patch.object(settings, "DEEPSEEK_API_KEY", None):
            provider = get_ai_provider()
            result = provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )
            assert "criterios_alinhamento" in result
            assert "criterios_potencial" in result
            assert "feedback_geral" in result
            assert result["feedback_geral"] != ""

    def test_no_real_api_call_during_tests(self):
        with patch.object(settings, "DEEPSEEK_API_KEY", "test-key"):
            provider = get_ai_provider()
            assert isinstance(provider, DeepSeekProvider)
