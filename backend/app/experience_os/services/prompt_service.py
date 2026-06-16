"""
PromptConstructionService — replicates the inline brain-context-prepend ternary
that previously lived in anthropic_provider.py and chat_provider.py, and is the
one place allowed to do provider-specific prompt formatting. Today there is
only one rendering style (a flat system-prompt string), since both LLM
providers consume the same shape.

Behaviour is byte-for-byte identical to before when called without a composed
prompt; see tests/test_prompt_service.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..composer import ComposedPrompt


def _render_composed(composed: ComposedPrompt) -> str:
    sections: list[str] = []

    def add(label: str, value: str | list[str]) -> None:
        if not value:
            return
        if isinstance(value, list):
            body = "\n".join(f"- {line}" for line in value)
        else:
            body = value
        sections.append(f"{label}:\n{body}" if isinstance(value, list) else f"{label}: {body}")

    add("Conversation Goal", composed.conversation_goal)
    add("Primary Emotional Objective", composed.primary_emotional_objective)
    add("Conversation Strategy", composed.conversation_strategy)
    add("Speech Instructions", composed.speech_instructions)
    add("Tone", composed.tone)
    if composed.vocabulary:
        add("Vocabulary", ", ".join(composed.vocabulary))
    add("Sentence Structure", composed.sentence_structure)
    add("Conversation Boundaries", composed.conversation_boundaries)
    add("Memory Usage Rules", composed.memory_usage_rules)
    add("Reflection Rules", composed.reflection_rules)
    add("Journey Rules", composed.journey_rules)

    return "\n\n".join(sections)


class DefaultPromptConstructionService:
    def build_system_prompt(
        self, brain_context: str | None, base_prompt: str, composed: ComposedPrompt | None = None
    ) -> str:
        base = (brain_context + "\n\n" + base_prompt) if brain_context else base_prompt
        if composed is None:
            return base
        rendered = _render_composed(composed)
        return f"{base}\n\n{rendered}" if rendered else base
