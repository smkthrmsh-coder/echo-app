from abc import ABC, abstractmethod

from app.models.emotion import EmotionProfile


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, profile: EmotionProfile, output_path: str) -> str:
        """Synthesize speech from profile.script. Returns path to audio file."""
        ...
