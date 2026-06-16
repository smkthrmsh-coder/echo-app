"""
ExperienceComposer — the intelligence layer between BlueprintRuntime and
PromptConstructionService. It interprets a Blueprint plus the rest of
ExperienceContext (Echo Brain memory, journey state, reflection rules,
speech/voice configuration) and produces a ComposedPrompt: structured,
model-agnostic prompt instructions. PromptConstructionService remains the
only component downstream that knows about any particular LLM provider's
prompt format.

compose() is pure — identical input always produces an identical
ComposedPrompt. Any future blending (merging multiple Blueprints) or adaptive
prompting (tuning behaviour from accumulated conversation history) must
happen upstream, by changing what's passed into compose(), never by adding
hidden state or randomness inside it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .fragments import DEFAULT_INTENTION_FRAGMENTS, FRAGMENTS, INTENTION_DEFAULT_FRAGMENTS
from .schema import Blueprint

if TYPE_CHECKING:
    from .context import ExperienceContext

# Tunable: how many lines the composed conversation strategy may contain before
# lower-priority tiers get dropped. Keeps the prompt from being overwhelmed with
# every applicable fragment at once.
MAX_CONVERSATION_STRATEGY_LINES = 4


@dataclass
class ComposedPrompt:
    conversation_goal: str
    primary_emotional_objective: str
    conversation_strategy: list[str]
    speech_instructions: list[str]
    tone: str
    vocabulary: list[str]
    sentence_structure: str
    conversation_boundaries: list[str]
    memory_usage_rules: list[str]
    reflection_rules: list[str]
    journey_rules: list[str]
    fragments_used: list[str] = field(default_factory=list)


class ExperienceComposer:
    def compose(
        self,
        ctx: ExperienceContext,
        current_message: str | None,
        previous_assistant_message: str | None,
        conversation_type: str,
    ) -> ComposedPrompt:
        blueprint = ctx.blueprint
        has_memory = bool(
            ctx.memories
            and ctx.memories.universal
            and blueprint.retrieval_strategy.use_universal_memory
        )

        strategy, fragments_used = self._conversation_strategy(
            blueprint, has_memory, current_message, previous_assistant_message, conversation_type
        )
        verify = has_memory and blueprint.context_verification.enabled

        return ComposedPrompt(
            conversation_goal=self._conversation_goal(blueprint),
            primary_emotional_objective=self._primary_emotional_objective(blueprint),
            conversation_strategy=strategy,
            speech_instructions=self._speech_instructions(ctx),
            tone=blueprint.speech_behaviour.warmth,
            vocabulary=list(blueprint.vocabulary_style.tone_words),
            sentence_structure=blueprint.sentence_structure.style,
            conversation_boundaries=self._conversation_boundaries(blueprint),
            memory_usage_rules=(
                [self._memory_verify_line(blueprint)] if verify
                else [FRAGMENTS["memory"]] if has_memory
                else [FRAGMENTS["memory_absent"]]
            ),
            reflection_rules=self._reflection_rules(blueprint),
            journey_rules=self._journey_rules(blueprint),
            fragments_used=fragments_used,
        )

    def _conversation_goal(self, blueprint: Blueprint) -> str:
        override = blueprint.prompt_instructions.base_prompt_override
        if override:
            return override
        goal = blueprint.emotional_objective.primary_goal
        if goal:
            return goal
        name = blueprint.identity.display_name or blueprint.identity.slug
        return f"Support the user through a {name} experience."

    def _memory_verify_line(self, blueprint: Blueprint) -> str:
        line = FRAGMENTS["memory_verify"]
        rules = blueprint.context_verification.rules
        return f"{line} ({'; '.join(rules)})" if rules else line

    def _primary_emotional_objective(self, blueprint: Blueprint) -> str:
        goal = blueprint.emotional_objective.primary_goal or "general emotional support"
        secondary = blueprint.emotional_objective.secondary_goals
        if secondary:
            return f"{goal} (also: {', '.join(secondary)})"
        return goal

    def _speech_instructions(self, ctx: ExperienceContext) -> list[str]:
        behaviour = ctx.speech_behaviour or {}
        lines = []
        if behaviour.get("pacing"):
            lines.append(f"Pace: {behaviour['pacing']}.")
        if behaviour.get("warmth"):
            lines.append(f"Warmth: {behaviour['warmth']}.")
        if behaviour.get("energy"):
            lines.append(f"Energy: {behaviour['energy']}.")
        lines.append(
            "Filler words are okay."
            if behaviour.get("fillers_allowed")
            else "Avoid filler words."
        )
        return lines

    def _conversation_boundaries(self, blueprint: Blueprint) -> list[str]:
        boundaries = [FRAGMENTS["safety"]]
        pause = blueprint.pause_behaviour
        if pause.enabled and pause.pause_style != "minimal":
            boundaries.append(FRAGMENTS["silence"])
        return boundaries

    def _reflection_rules(self, blueprint: Blueprint) -> list[str]:
        rules = blueprint.reflection_rules
        if not rules.enabled:
            return []
        line = FRAGMENTS["reflection"]
        if rules.frequency:
            line = f"{line} (frequency: {rules.frequency})"
        return [line]

    def _journey_rules(self, blueprint: Blueprint) -> list[str]:
        strategy = blueprint.journey_strategy
        if not strategy.enabled:
            return []
        line = FRAGMENTS["journey"]
        if strategy.journey_slug:
            line = f"{line} (journey: {strategy.journey_slug})"
        return [line]

    def _conversation_strategy(
        self,
        blueprint: Blueprint,
        has_memory: bool,
        current_message: str | None,
        previous_assistant_message: str | None,
        conversation_type: str,
    ) -> tuple[list[str], list[str]]:
        # Priority order, highest first: current conversation > Echo Brain memory >
        # journey state > reflection > user profile (no-op today, no data exists yet)
        # > explicit blueprint style notes > generic intention-default fragments.
        candidates: list[tuple[str, str]] = []

        if current_message or previous_assistant_message:
            key = "conversation_reply" if conversation_type == "reply" else "conversation_initial"
            candidates.append((key, FRAGMENTS[key]))

        if has_memory:
            if blueprint.context_verification.enabled:
                candidates.append(("memory_verify", self._memory_verify_line(blueprint)))
            else:
                candidates.append(("memory", FRAGMENTS["memory"]))

        if blueprint.journey_strategy.enabled:
            candidates.append(("journey", FRAGMENTS["journey"]))

        if blueprint.reflection_rules.enabled:
            candidates.append(("reflection", FRAGMENTS["reflection"]))

        for note in blueprint.prompt_instructions.style_notes:
            candidates.append(("style_note", note))

        intention_key = blueprint.voice_configuration.voice_intention.lower()
        for key in INTENTION_DEFAULT_FRAGMENTS.get(intention_key, DEFAULT_INTENTION_FRAGMENTS):
            candidates.append((key, FRAGMENTS[key]))

        strategy: list[str] = []
        fragments_used: list[str] = []
        seen_text: set[str] = set()
        for key, text in candidates:
            if text in seen_text:
                continue
            seen_text.add(text)
            strategy.append(text)
            fragments_used.append(key)
            if len(strategy) >= MAX_CONVERSATION_STRATEGY_LINES:
                break

        return strategy, fragments_used
