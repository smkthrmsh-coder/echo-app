import asyncio
from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.speech_recognition.base import SpeechRecognitionProvider, TranscriptionResult

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_model():
    """Load Whisper model once and cache it (slow first load, fast subsequent calls)."""
    from faster_whisper import WhisperModel

    settings = get_settings()
    logger.info(f"Loading Whisper model: {settings.whisper_model} on {settings.whisper_device}")
    model = WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type="int8",
    )
    logger.info("Whisper model loaded.")
    return model


class WhisperProvider(SpeechRecognitionProvider):
    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        logger.info(f"Transcribing: {audio_path}")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run_transcription, audio_path)
        return result

    def _run_transcription(self, audio_path: str) -> TranscriptionResult:
        model = _load_model()
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        logger.info(f"Transcribed: {text!r} (lang={info.language})")
        return TranscriptionResult(
            text=text,
            language=info.language,
            confidence=info.language_probability,
        )
