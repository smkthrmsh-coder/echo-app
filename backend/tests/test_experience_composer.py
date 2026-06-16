"""Tests for ExperienceComposer — turns a Blueprint + ExperienceContext into a ComposedPrompt."""

from app.brain.schema import MemoryBundle
from app.experience_os.composer import ComposedPrompt, ExperienceComposer
from app.experience_os.context import ExperienceContext
from app.experience_os.fragments import FRAGMENTS
from app.experience_os.schema import Blueprint
from app.experience_os.services.prompt_service import DefaultPromptConstructionService


def _blueprint(**overrides) -> Blueprint:
    data = {"identity": {"slug": "test-blueprint", "display_name": "Test Blueprint"}}
    data.update(overrides)
    return Blueprint(**data)


def _ctx(
    blueprint: Blueprint, memories: MemoryBundle | None = None, **overrides
) -> ExperienceContext:
    defaults = dict(
        user_id="user-1",
        intention=blueprint.voice_configuration.voice_intention,
        blueprint=blueprint,
        brain_context=memories.universal if memories else "",
        memories=memories,
        speech_behaviour={
            "pacing": blueprint.speech_behaviour.pacing,
            "warmth": blueprint.speech_behaviour.warmth,
            "energy": blueprint.speech_behaviour.energy,
            "fillers_allowed": blueprint.speech_behaviour.fillers_allowed,
        },
    )
    defaults.update(overrides)
    return ExperienceContext(**defaults)


def test_compose_basic_default_blueprint():
    blueprint = _blueprint()
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint), None, None, "initial")

    assert composed.conversation_goal
    assert composed.tone == blueprint.speech_behaviour.warmth
    assert composed.sentence_structure == blueprint.sentence_structure.style
    assert FRAGMENTS["safety"] in composed.conversation_boundaries


def test_intention_default_fragments_peace():
    blueprint = _blueprint(voice_configuration={"voice_intention": "peace"})
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint), None, None, "initial")

    assert FRAGMENTS["grounding"] in composed.conversation_strategy
    assert FRAGMENTS["silence"] in composed.conversation_strategy


def test_intention_default_fragments_motivation():
    blueprint = _blueprint(voice_configuration={"voice_intention": "motivation"})
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint), None, None, "initial")

    assert FRAGMENTS["motivation"] in composed.conversation_strategy


def test_memory_tier_outranks_blueprint_defaults():
    blueprint = _blueprint(voice_configuration={"voice_intention": "comfort"})
    memories = MemoryBundle(universal="likes long walks")
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint, memories=memories), None, None, "initial")

    assert FRAGMENTS["memory"] in composed.conversation_strategy
    assert FRAGMENTS["empathy"] in composed.conversation_strategy
    memory_index = composed.conversation_strategy.index(FRAGMENTS["memory"])
    empathy_index = composed.conversation_strategy.index(FRAGMENTS["empathy"])
    assert memory_index < empathy_index


def test_context_prioritization_caps_and_drops_lowest_tier_first():
    blueprint = _blueprint(
        voice_configuration={"voice_intention": "peace"},
        journey_strategy={"enabled": True, "journey_slug": "calm-week"},
        reflection_rules={"enabled": True},
    )
    memories = MemoryBundle(universal="prefers quiet mornings")
    composer = ExperienceComposer()
    composed = composer.compose(
        _ctx(blueprint, memories=memories), "I'm anxious today", None, "initial"
    )

    # 6 candidates exist (conversation, memory, journey, reflection, grounding, silence)
    # but the cap keeps only the 4 highest-priority ones.
    assert len(composed.conversation_strategy) <= 4
    assert FRAGMENTS["memory"] in composed.conversation_strategy
    assert FRAGMENTS["grounding"] not in composed.conversation_strategy
    assert FRAGMENTS["silence"] not in composed.conversation_strategy


def test_context_verification_enabled_uses_verify_fragment_instead_of_memory():
    blueprint = _blueprint(
        voice_configuration={"voice_intention": "comfort"},
        context_verification={"enabled": True, "rules": ["confirm before assuming"]},
    )
    memories = MemoryBundle(universal="has an interview coming up")
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint, memories=memories), None, None, "initial")

    assert FRAGMENTS["memory"] not in composed.conversation_strategy
    assert FRAGMENTS["memory"] not in composed.memory_usage_rules
    verify_line = composed.memory_usage_rules[0]
    assert FRAGMENTS["memory_verify"] in verify_line
    assert "confirm before assuming" in verify_line
    assert verify_line in composed.conversation_strategy


def test_minimal_pause_style_omits_silence_boundary():
    blueprint = _blueprint(
        voice_configuration={"voice_intention": "energy"},
        pause_behaviour={"enabled": True, "pause_style": "minimal"},
    )
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint), None, None, "initial")

    assert FRAGMENTS["silence"] not in composed.conversation_boundaries
    assert FRAGMENTS["safety"] in composed.conversation_boundaries


def test_non_minimal_pause_style_includes_silence_boundary():
    blueprint = _blueprint(
        voice_configuration={"voice_intention": "peace"},
        pause_behaviour={"enabled": True, "pause_style": "long_reflective"},
    )
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint), None, None, "initial")

    assert FRAGMENTS["silence"] in composed.conversation_boundaries


def test_missing_memory_falls_back_gracefully():
    blueprint = _blueprint()
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint, memories=None), None, None, "initial")

    assert composed.memory_usage_rules == [FRAGMENTS["memory_absent"]]
    assert "memory" not in composed.fragments_used


def test_missing_optional_blueprint_fields_does_not_crash():
    blueprint = Blueprint(identity={"slug": "bare"})
    composer = ExperienceComposer()
    composed = composer.compose(_ctx(blueprint), None, None, "initial")

    assert composed.conversation_goal
    assert composed.memory_usage_rules == [FRAGMENTS["memory_absent"]]
    assert composed.reflection_rules == []
    assert composed.journey_rules == []


def test_prompt_stability_same_input_same_output():
    blueprint = _blueprint(voice_configuration={"voice_intention": "sleep"})
    memories = MemoryBundle(universal="winds down with reading")
    ctx = _ctx(blueprint, memories=memories)
    composer = ExperienceComposer()

    first = composer.compose(ctx, "good night", None, "initial")
    second = composer.compose(ctx, "good night", None, "initial")

    assert first == second


def test_prompt_construction_service_legacy_path_unchanged_without_composed():
    service = DefaultPromptConstructionService()
    assert service.build_system_prompt("brain", "base") == "brain\n\nbase"
    assert service.build_system_prompt(None, "base") == "base"


def test_prompt_construction_service_renders_composed_sections():
    composed = ComposedPrompt(
        conversation_goal="Help the user unwind.",
        primary_emotional_objective="calm",
        conversation_strategy=[FRAGMENTS["grounding"]],
        speech_instructions=["Pace: slow."],
        tone="warm",
        vocabulary=["gentle", "soft"],
        sentence_structure="flowing",
        conversation_boundaries=[FRAGMENTS["safety"]],
        memory_usage_rules=[FRAGMENTS["memory_absent"]],
        reflection_rules=[],
        journey_rules=[],
        fragments_used=["grounding", "safety", "memory_absent"],
    )
    service = DefaultPromptConstructionService()
    rendered = service.build_system_prompt(None, "You are Echo.", composed)

    assert "You are Echo." in rendered
    assert "Conversation Goal: Help the user unwind." in rendered
    assert "Conversation Strategy:" in rendered
    assert FRAGMENTS["grounding"] in rendered
    assert "Vocabulary: gentle, soft" in rendered
    assert "Reflection Rules" not in rendered
