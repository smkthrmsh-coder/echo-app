"""Tests for BlueprintEngine — voice ID resolution must never drift from voice_mapping.py."""

from app.experience_os.blueprint_engine import BlueprintEngine
from app.services.llm.voice_mapping import INTENTION_VOICE_MAP


def test_every_intention_blueprint_loads_and_resolves_voice():
    engine = BlueprintEngine()
    for intention, iv in INTENTION_VOICE_MAP.items():
        blueprint = engine.load(intention)
        vc = blueprint.voice_configuration
        assert vc.resolved_male_voice_id == iv.male_id
        assert vc.resolved_female_voice_id == iv.female_id
        assert vc.resolved_stability == iv.stability
        assert vc.resolved_similarity_boost == iv.similarity_boost
        assert vc.resolved_style == iv.style


def test_default_blueprint_loads():
    engine = BlueprintEngine()
    blueprint = engine.load("default")
    assert blueprint.identity.slug == "default"


def test_unknown_slug_falls_back_to_default_without_raising():
    engine = BlueprintEngine()
    blueprint = engine.load("not-a-real-slug")
    assert blueprint.identity.slug == "default"


def test_none_intention_falls_back_to_default():
    engine = BlueprintEngine()
    blueprint = engine.load(None)
    assert blueprint.identity.slug == "default"


def test_loaded_blueprints_are_cached():
    engine = BlueprintEngine()
    first = engine.load("peace")
    second = engine.load("peace")
    assert first is second


def test_peace_blueprint_is_fully_configured():
    engine = BlueprintEngine()
    blueprint = engine.load("peace")
    assert blueprint.pause_behaviour.enabled is True
    assert blueprint.context_verification.enabled is True
    assert blueprint.context_verification.rules
    assert blueprint.prompt_instructions.style_notes
    assert blueprint.background_music_strategy.tone_ambience_key == "calm"
    assert blueprint.vocabulary_style.tone_words


V1_INTENTIONS = [
    "peace", "motivation", "confidence", "comfort", "sleep",
    "focus", "clarity", "energy", "encouragement",
]


def test_every_v1_intention_blueprint_is_fully_configured():
    engine = BlueprintEngine()
    for slug in V1_INTENTIONS:
        blueprint = engine.load(slug)
        assert blueprint.pause_behaviour.enabled is True, slug
        assert blueprint.context_verification.enabled is True, slug
        assert blueprint.context_verification.rules, slug
        assert blueprint.prompt_instructions.style_notes, slug
        assert blueprint.vocabulary_style.tone_words, slug
        assert blueprint.emotional_objective.primary_goal, slug


def test_fast_intentions_use_minimal_pause_style():
    engine = BlueprintEngine()
    for slug in ["motivation", "focus", "energy"]:
        assert engine.load(slug).pause_behaviour.pause_style == "minimal", slug
