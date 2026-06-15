import asyncio
from pathlib import Path
from typing import ClassVar

from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings as ELVoiceSettings

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.emotion import EmotionProfile
from app.services.tts.base import TTSProvider

logger = get_logger(__name__)

# Character-style voices first — more expressive, more natural-sounding accents.
# Probe skips any voice that isn't accessible (plan or not-found). Falls through to legacy.
_CANDIDATES_FEMALE = [
    # Characters use-case — expressive, less robotic
    ("Charlotte",  "XB0fDUnXU5powFXDhCwa"),  # American, character
    ("Matilda",    "XrExE9yKIg1WjnnlVkGX"),  # American, warm natural
    ("Alice",      "Xb7hH8MSUJpSbSDYk0k2"),  # British, clear character
    ("Aria",       "9BWtsMINqrJLrRacOk9x"),  # American, friendly
    ("River",      "SAz9YHcvj6GT2YYXdXww"),  # Calm, confident
    ("Jessica",    "cgSgspJ2msm6clMCkdW9"),  # American
    ("Laura",      "FGY2WhTYpPnrIDTdsKH5"),  # American
    # Legacy fallbacks
    ("Rachel",     "21m00Tcm4TlvDq8ikWAM"),
    ("Bella",      "EXAVITQu4vr4xnSDxMaL"),
]

_CANDIDATES_MALE = [
    # Characters use-case
    ("Harry",    "SOYHLrjzK2X1ezoPC6cr"),   # American, warm character
    ("Callum",   "N2lVS1w4EtoT3dr4eOWO"),   # American, intense character
    ("Daniel",   "onwK4e9ZLuTAKqWW03F9"),   # British, deep
    ("Charlie",  "IKne3meq5aSn9XLyUdCD"),   # Australian, natural
    ("Liam",     "TX3LPaxmHKxFdv7VOFE1"),   # American
    ("Brian",    "nPczCjzI2devNBz1zQrb"),   # American
    # Legacy fallbacks
    ("Adam",     "pNInz6obpgDQGcFmaJgB"),
    ("Antoni",   "ErXwobaYiN019PkySvjV"),
]


def _is_skippable_error(exc: Exception) -> bool:
    """True for errors that mean 'this voice isn't accessible' — probe should skip, not crash."""
    s = str(exc).lower()
    return any(k in s for k in (
        "paid_plan_required", "402", "payment_required",
        "404", "not_found", "voice_not_found", "invalid_voice_id",
        "400", "422", "validation",
    ))


class ElevenLabsTTSProvider(TTSProvider):
    # Cached at class level — probe runs once per process
    _probe_female: ClassVar[str | None] = None
    _probe_male: ClassVar[str | None] = None
    _probe_done: ClassVar[bool] = False

    def __init__(self) -> None:
        settings = get_settings()
        self._client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self._model = settings.elevenlabs_tts_model
        # Environment-level overrides (user can set ELEVENLABS_VOICE_ID in .env)
        self._env_voice_id = settings.elevenlabs_voice_id or ""
        self._env_voice_id_male = settings.elevenlabs_voice_id_male or ""

    def _convert_sync(self, voice_id: str, text: str, vs: ELVoiceSettings) -> bytes:
        return b"".join(
            self._client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=self._model,
                voice_settings=vs,
                output_format="mp3_44100_128",
            )
        )

    def _probe_voice(self, voice_id: str) -> bool:
        """Try a tiny TTS. Returns True if the voice is usable, False if skippable (plan/not-found)."""
        try:
            vs = ELVoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=False)
            self._convert_sync(voice_id, "Ok.", vs)
            return True
        except Exception as exc:
            if _is_skippable_error(exc):
                return False
            raise  # unexpected (network, auth, etc.) — propagate

    def _run_probe(self) -> None:
        if ElevenLabsTTSProvider._probe_done:
            return
        logger.info("Probing ElevenLabs voices to find available ones for this plan…")

        for name, vid in _CANDIDATES_FEMALE:
            logger.info(f"  Probing female voice: {name} ({vid})")
            if self._probe_voice(vid):
                ElevenLabsTTSProvider._probe_female = vid
                logger.info(f"  ✓ Female voice available: {name} ({vid})")
                break
            logger.info(f"  ✗ {name} not available on this plan")

        for name, vid in _CANDIDATES_MALE:
            logger.info(f"  Probing male voice: {name} ({vid})")
            if self._probe_voice(vid):
                ElevenLabsTTSProvider._probe_male = vid
                logger.info(f"  ✓ Male voice available: {name} ({vid})")
                break
            logger.info(f"  ✗ {name} not available on this plan")

        ElevenLabsTTSProvider._probe_done = True
        if not ElevenLabsTTSProvider._probe_female and not ElevenLabsTTSProvider._probe_male:
            logger.error(
                "No ElevenLabs voices available on this plan. "
                "Set ELEVENLABS_VOICE_ID in backend/.env with a voice ID from your account."
            )

    def _pick_fallback(self, gender: str) -> str | None:
        """Return the best available fallback voice ID for the given gender."""
        # 1. Environment override
        if gender == "male" and self._env_voice_id_male:
            return self._env_voice_id_male
        if self._env_voice_id:
            return self._env_voice_id

        # 2. Probed result
        if gender == "male":
            return ElevenLabsTTSProvider._probe_male or ElevenLabsTTSProvider._probe_female
        return ElevenLabsTTSProvider._probe_female or ElevenLabsTTSProvider._probe_male

    async def synthesize(self, profile: EmotionProfile, output_path: str) -> str:
        logger.info(f"Synthesizing TTS | voice={profile.voice_name} | model={self._model}")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        vs = profile.voice_settings
        voice_settings = ELVoiceSettings(
            stability=vs.stability,
            similarity_boost=vs.similarity_boost,
            style=vs.style,
            use_speaker_boost=vs.use_speaker_boost,
        )

        loop = asyncio.get_event_loop()

        primary_id = self._env_voice_id or profile.voice_id or None

        if primary_id:
            try:
                audio = await loop.run_in_executor(
                    None, lambda: self._convert_sync(primary_id, profile.script, voice_settings)
                )
                Path(output_path).write_bytes(audio)
                logger.info(f"TTS saved: {output_path} ({len(audio):,} bytes)")
                return output_path
            except Exception as exc:
                if not _is_skippable_error(exc):
                    raise
                logger.warning(f"Voice {primary_id} not accessible — running probe")

        # Run probe (once) to find a working voice
        await loop.run_in_executor(None, self._run_probe)

        # Infer gender from intention voice mapping
        gender = "female"
        from app.services.llm.voice_mapping import INTENTION_VOICE_MAP
        for iv in INTENTION_VOICE_MAP.values():
            if profile.voice_id in (iv.male_id, iv.female_id):
                gender = "male" if profile.voice_id == iv.male_id else "female"
                break

        fallback_id = self._pick_fallback(gender)
        if not fallback_id:
            raise RuntimeError(
                "No ElevenLabs voices are accessible on this plan. "
                "Please set ELEVENLABS_VOICE_ID=<your-voice-id> in backend/.env. "
                "Find voice IDs at elevenlabs.io → Voices."
            )

        logger.info(f"Retrying with probed fallback voice: {fallback_id}")
        try:
            audio = await loop.run_in_executor(
                None, lambda: self._convert_sync(fallback_id, profile.script, voice_settings)
            )
            Path(output_path).write_bytes(audio)
            logger.info(f"TTS saved (fallback): {output_path} ({len(audio):,} bytes)")
            return output_path
        except Exception as exc:
            raise RuntimeError(
                f"ElevenLabs TTS failed on fallback voice {fallback_id}. "
                "Please set ELEVENLABS_VOICE_ID in backend/.env."
            ) from exc
