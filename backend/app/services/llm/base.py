from abc import ABC, abstractmethod

from app.models.emotion import EmotionProfile


class LLMProvider(ABC):
    @abstractmethod
    async def analyze_and_generate(self, prompt: str) -> EmotionProfile:
        """Analyze user prompt, determine emotion profile, and write narration script."""
        ...
