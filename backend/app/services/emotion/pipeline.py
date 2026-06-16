"""
Voice Emotion Pipeline Orchestrator.

Coordinates: LLM → TTS → Save
Ambience is handled browser-side via Web Audio API (removes it from the critical path).
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
from app.services.llm.factory import get_llm_provider
from app.services.llm.pacing import apply_pacing_markup
from app.services.tts.factory import get_tts_provider

if TYPE_CHECKING:
    from app.experience_os.composer import ComposedPrompt

logger = get_logger(__name__)


async def run_pipeline(
    prompt: str,
    celebrity_voice_id: str | None = None,
    gender: str | None = None,
    speaking_styles: list[str] | None = None,
    username: str = "there",
    intention: str | None = None,
    brain_context: str | None = None,
    composed_prompt: "ComposedPrompt | None" = None,
    pause_behaviour_enabled: bool = False,
) -> tuple[EmotionProfile, str, float]:
    """
    Full pipeline: prompt → EmotionProfile + voice audio file.
    Returns (emotion_profile, audio_path, duration_seconds).
    """
    settings = get_settings()
    generation_id = str(uuid.uuid4())
    audio_dir = Path(settings.audio_output_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    final_path = str(audio_dir / f"{generation_id}_voice.mp3")

    t0 = time.monotonic()

    # Step 1: LLM analyzes prompt → emotion profile + script
    logger.info(f"[{generation_id}] Step 1: LLM analysis | intention={intention} | gender={gender}")
    llm = get_llm_provider()
    profile = await llm.analyze_and_generate(
        prompt,
        user_gender=gender,
        user_styles=speaking_styles,
        username=username,
        intention=intention,
        brain_context=brain_context,
        composed_prompt=composed_prompt,
    )
    t1 = time.monotonic()
    logger.info(
        f"[{generation_id}] LLM done in {t1-t0:.2f}s | tone={profile.tone.value} | "
        f"script_len={len(profile.script.split())} words"
    )

    if celebrity_voice_id:
        profile.voice_id = celebrity_voice_id
        profile.voice_name = f"custom:{celebrity_voice_id}"

    if not profile.script:
        raise RuntimeError("LLM returned empty script")

    if pause_behaviour_enabled:
        profile.script = apply_pacing_markup(profile.script, intention=intention)

    # Step 2: TTS → voice audio
    logger.info(f"[{generation_id}] Step 2: TTS synthesis | voice_id={profile.voice_id}")
    tts = get_tts_provider()
    await tts.synthesize(profile, final_path)
    t2 = time.monotonic()
    logger.info(f"[{generation_id}] TTS done in {t2-t1:.2f}s")

    duration = get_audio_duration(final_path)
    if pause_behaviour_enabled:
        silence_ms = TRAILING_SILENCE_MS.get(intention, DEFAULT_TRAILING_SILENCE_MS)
        duration = append_trailing_silence(final_path, silence_ms)
    logger.info(
        f"[{generation_id}] Pipeline complete | total={t2-t0:.2f}s | "
        f"duration={duration:.1f}s | {final_path}"
    )
    return profile, final_path, duration
