"""ExperienceContext — the shared state passed through Experience OS for a single turn."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.brain.schema import MemoryBundle

from .composer import ComposedPrompt
from .events import RuntimeEvent
from .schema import Blueprint


@dataclass
class VoiceSelection:
    voice_id: str
    gender: str


@dataclass
class ExperienceContext:
    user_id: str
    intention: str | None
    blueprint: Blueprint
    brain_context: str
    memories: MemoryBundle | None = None
    conversation_history: list[dict] = field(default_factory=list)
    user_profile: dict[str, Any] | None = None
    journey_state: dict[str, Any] | None = None
    reflection_summary: str | None = None
    voice_selection: VoiceSelection | None = None
    music_playlist: str | None = None
    speech_behaviour: dict[str, Any] | None = None
    prompt_instructions: str | None = None
    composed_prompt: ComposedPrompt | None = None
    events: list[RuntimeEvent] = field(default_factory=list)
