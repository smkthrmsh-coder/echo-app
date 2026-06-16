"""
Service interfaces for everything Experience OS orchestrates.

These are Protocols, not ABCs — concrete implementations in services/ wrap the
existing, working implementations without changing their behaviour. This sprint
proves decoupling; it does not change what any of these services actually do.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .composer import ComposedPrompt


class VoiceSelectionService(Protocol):
    def select_voice(self, intention: str | None, gender_preference: str | None) -> tuple[str, str]:
        """Return (voice_id, resolved_gender)."""
        ...


class MusicSelectionService(Protocol):
    def select_ambience(self, tone: str) -> str:
        """Return an ambience description string for the given tone."""
        ...


class PromptConstructionService(Protocol):
    def build_system_prompt(
        self, brain_context: str | None, base_prompt: str, composed: ComposedPrompt | None = None
    ) -> str:
        """Combine brain context, a base system prompt, and optional composed instructions."""
        ...


class JourneyService(Protocol):
    def is_enabled(self) -> bool:
        ...


class ReflectionService(Protocol):
    def is_enabled(self) -> bool:
        ...


class HumanSpeechService(Protocol):
    def is_enabled(self) -> bool:
        ...
