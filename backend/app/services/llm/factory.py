from app.core.config import get_settings
from app.services.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    raise ValueError(f"Unsupported LLM provider: {provider!r}. Supported: ['anthropic']")
