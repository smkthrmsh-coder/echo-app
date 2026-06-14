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

        # ElevenLabs sound generation supports 0.5 to 22 seconds per request
        # For longer ambience, we generate a chunk and it will be looped by the mixer
        clamped_duration = min(max(duration_seconds, 0.5), 22.0)

        payload = {
            "text": prompt,
            "duration_seconds": clamped_duration,
            "prompt_influence": 0.3,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                SOUND_GEN_URL,
                json=payload,
                headers={
                    "xi-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                logger.error(
                    f"ElevenLabs Sound API error: {response.status_code} — {response.text[:200]}"
                )
                raise RuntimeError(
                    f"Ambience generation failed: HTTP {response.status_code}"
                )

            Path(output_path).write_bytes(response.content)

        logger.info(f"Ambience saved: {output_path} ({len(response.content):,} bytes)")
        return output_path
