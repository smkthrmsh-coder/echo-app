"""
Chat reply pipeline — voice audio only.
Ambience is handled browser-side (removed from server critical path for responsiveness).
"""

import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.emotion import EmotionProfile
from app.services.audio.mixer import (
    DEFAULT_TRAILING_SILENCE_MS,
    TRAILING_SILENCE_MS,
    append_trailing_silence,
    get_audio_duration,
)
from app.services.llm.chat_provider import ChatProvider
from app.services.tts.factory import get_tts_provider

if TYPE_CHECKING:
    from app.experience_os.composer import ComposedPrompt

logger = get_logger(__name__)


async def run_chat_pipeline(
    user_message: str,
    history: list[dict],
    speaking_styles: list[str],
    gender: str,
    energy_level: int,
    emotional_mode: bool = True,
    celebrity_voice_id: str | None = None,
    locked_voice_id: str | None = None,
    locked_voice_name: str | None = None,
    intention: str | None = None,
    brain_context: str | None = None,
    composed_prompt: "ComposedPrompt | None" = None,
    pause_behaviour_enabled: bool = False,
    speech_rate_override: float | None = None,
) -> tuple[EmotionProfile, str, float]:
    """
    Chat reply pipeline: message → EmotionProfile + voice audio.
    Returns (profile, audio_path, duration_seconds).
    """
    settings = get_settings()
    generation_id = str(uuid.uuid4())
    audio_dir = Path(settings.audio_output_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    final_path = str(audio_dir / f"{generation_id}_chat.mp3")

    t0 = time.monotonic()

    # Step 1: LLM generates reply
    chat = ChatProvider()
    profile = await chat.generate_reply(
        user_message=user_message,
        history=history,
        speaking_styles=speaking_styles,
        gender=gender,
        energy_level=energy_level,
        emotional_mode=emotional_mode,
        locked_voice_id=locked_voice_id,
        locked_voice_name=locked_voice_name,
        intention=intention,
        brain_context=brain_context,
        composed_prompt=composed_prompt,
        pause_behaviour_enabled=pause_behaviour_enabled,
        speech_rate_override=speech_rate_override,
    )
    t1 = time.monotonic()
    logger.info(
        f"[{generation_id}] Chat LLM done in {t1-t0:.2f}s | tone={profile.tone.value} | "
        f"script_len={len(profile.script.split())} words | emotional={emotional_mode}"
    )

    if celebrity_voice_id:
        profile.voice_id = celebrity_voice_id
        profile.voice_name = f"custom:{celebrity_voice_id}"

    # Step 2: TTS
    tts = get_tts_provider()
    await tts.synthesize(profile, final_path)
    t2 = time.monotonic()

    duration = get_audio_duration(final_path)
    if pause_behaviour_enabled:
        silence_ms = TRAILING_SILENCE_MS.get(intention, DEFAULT_TRAILING_SILENCE_MS)
        duration = append_trailing_silence(final_path, silence_ms)
    logger.info(
        f"[{generation_id}] Chat pipeline done | total={t2-t0:.2f}s | duration={duration:.1f}s"
    )
    return profile, final_path, duration
