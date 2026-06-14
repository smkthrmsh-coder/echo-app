from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    language: str | None = None
    confidence: float | None = None


class SpeechRecognitionProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio file to text."""
        ...
