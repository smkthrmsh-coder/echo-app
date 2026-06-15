"""
Voice Emotion Pipeline Orchestrator.

Coordinates: LLM → TTS + Ambience (parallel) → Mix → Save
Ambience failure is non-fatal — falls back to voice-only audio.
"""

import asyncio
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.emotion import EmotionProfile
from app.services.ambience.elevenlabs_provider import ElevenLabsAmbienceProvider
from app.services.audio.mixer import get_audio_duration, mix_audio
from app.services.llm.factory import get_llm_provider
from app.services.tts.factory import get_tts_provider

logger = get_logger(__name__)


async def _try_ambience(provider: ElevenLabsAmbienceProvider, prompt: str, output_path: str) -> str | None:
    """Generate ambience audio, returning None on any failure (non-fatal)."""
    try:
        return await provider.generate(prompt=prompt, output_path=output_path, duration_seconds=22.0)
    except Exception as exc:
        logger.warning(f"Ambience generation failed (voice-only fallback): {exc}")
        return None


async def run_pipeline(
    prompt: str,
    celebrity_voice_id: str | None = None,
    gender: str | None = None,
    speaking_styles: list[str] | None = None,
    username: str = "there",
    intention: str | None = None,
) -> tuple[EmotionProfile, str, float]:
    """
    Full pipeline: prompt → EmotionProfile + mixed audio file.
    Returns (emotion_profile, audio_path, duration_seconds).
    """
    settings = get_settings()
    generation_id = str(uuid.uuid4())
    audio_dir = Path(settings.audio_output_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)

    voice_path = str(audio_dir / f"{generation_id}_voice.mp3")
    ambience_path = str(audio_dir / f"{generation_id}_ambience.mp3")
    final_path = str(audio_dir / f"{generation_id}_final.mp3")

    # Step 1: LLM analyzes prompt → emotion profile + script
    logger.info(f"[{generation_id}] Step 1: LLM analysis")
    llm = get_llm_provider()
    profile = await llm.analyze_and_generate(
        prompt,
        user_gender=gender,
        user_styles=speaking_styles,
        username=username,
        intention=intention,
    )
    logger.info(
        f"[{generation_id}] Profile: tone={profile.tone.value}, "
        f"voice={profile.voice_name}, pacing={profile.pacing.value}"
    )

    if celebrity_voice_id:
        profile.voice_id = celebrity_voice_id
        profile.voice_name = f"custom:{celebrity_voice_id}"
        logger.info(f"[{generation_id}] Using celebrity voice override: {celebrity_voice_id}")

    if not profile.script:
        raise RuntimeError("LLM returned empty script")

    # Step 2: TTS + Ambience in parallel (ambience failure is non-fatal)
    logger.info(f"[{generation_id}] Step 2: Parallel TTS + Ambience generation")
    tts = get_tts_provider()
    ambience_provider = ElevenLabsAmbienceProvider()

    voice_result, ambience_result = await asyncio.gather(
        tts.synthesize(profile, voice_path),
        _try_ambience(ambience_provider, profile.ambience_prompt, ambience_path),
    )

    # Step 3: Mix if ambience available, otherwise use voice directly
    if ambience_result:
        logger.info(f"[{generation_id}] Step 3: Mixing audio")
        final_path, duration = mix_audio(
            voice_path=voice_result,
            ambience_path=ambience_result,
            output_path=final_path,
            ambience_volume_db=profile.ambience_volume_db,
            voice_volume_db=settings.voice_volume_db,
        )
        Path(voice_path).unlink(missing_ok=True)
        Path(ambience_path).unlink(missing_ok=True)
    else:
        logger.info(f"[{generation_id}] Step 3: Voice-only (no ambience)")
        Path(voice_result).rename(final_path)
        duration = get_audio_duration(final_path)

    logger.info(f"[{generation_id}] Pipeline complete | duration={duration:.1f}s | {final_path}")
    return profile, final_path, duration
