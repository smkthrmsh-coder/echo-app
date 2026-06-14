from app.core.config import get_settings
from app.services.tts.base import TTSProvider


def get_tts_provider() -> TTSProvider:
    settings = get_settings()
    provider = settings.tts_provider.lower()

    if provider == "elevenlabs":
        from app.services.tts.elevenlabs_provider import ElevenLabsTTSProvider
        return ElevenLabsTTSProvider()

    raise ValueError(f"Unsupported TTS provider: {provider!r}. Supported: ['elevenlabs']")
