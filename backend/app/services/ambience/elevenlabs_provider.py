from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.ambience.base import AmbienceProvider

logger = get_logger(__name__)

SOUND_GEN_URL = "https://api.elevenlabs.io/v1/sound-generation"


class ElevenLabsAmbienceProvider(AmbienceProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.elevenlabs_api_key

    async def generate(
        self, prompt: str, output_path: str, duration_seconds: float = 30.0
    ) -> str:
        logger.info(f"Generating ambience | prompt={prompt[:60]!r} | duration={duration_seconds}s")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        clamped_duration = min(max(duration_seconds, 0.5), 22.0)
        fallback_prompt = "soft gentle ambient background texture"
        prompts_to_try = [prompt, fallback_prompt]

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt, try_prompt in enumerate(prompts_to_try):
                payload = {
                    "text": try_prompt,
                    "duration_seconds": clamped_duration,
                    "prompt_influence": 0.3,
                }
                try:
                    response = await client.post(
                        SOUND_GEN_URL,
                        json=payload,
                        headers={
                            "xi-api-key": self._api_key,
                            "Content-Type": "application/json",
                        },
                    )
                    if response.status_code == 200:
                        Path(output_path).write_bytes(response.content)
                        logger.info(f"Ambience saved (attempt {attempt + 1}): {output_path} ({len(response.content):,} bytes)")
                        return output_path
                    logger.warning(
                        f"Ambience attempt {attempt + 1} failed: HTTP {response.status_code} — {response.text[:300]}"
                    )
                except Exception as exc:
                    logger.warning(f"Ambience attempt {attempt + 1} exception: {exc}")

        raise RuntimeError(f"Ambience generation failed after {len(prompts_to_try)} attempts")
