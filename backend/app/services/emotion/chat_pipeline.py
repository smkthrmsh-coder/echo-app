"""
Chat reply pipeline — voice audio only.
Ambience is handled browser-side (removed from server critical path for responsiveness).
"""

import time
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.emotion import EmotionProfile
from app.services.audio.mixer import get_audio_duration
from app.services.llm.chat_provider import ChatProvider
from app.services.tts.factory import get_tts_provider

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
    logger.info(
        f"[{generation_id}] Chat pipeline done | total={t2-t0:.2f}s | duration={duration:.1f}s"
    )
    return profile, final_path, duration
