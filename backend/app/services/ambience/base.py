from abc import ABC, abstractmethod


class AmbienceProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, output_path: str, duration_seconds: float = 30.0) -> str:
        """Generate ambient audio from a text prompt. Returns path to audio file."""
        ...
