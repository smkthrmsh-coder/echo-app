"""Tests for BlueprintRuntime — the Experience Lifecycle executor."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.db.database import Base, SessionLocal, get_engine
from app.db.models import Conversation
from app.experience_os.runtime import BlueprintRuntime
from app.experience_os.schema import Blueprint
from app.experience_os.validation import blueprint_warnings, validate_blueprint
from app.models.emotion import EmotionalTone, EmotionProfile, NarrationStyle, Pacing, VoiceSettings
from app.services.llm.voice_mapping import INTENTION_VOICE_MAP, get_voice_for_intention

EXPECTED_PREP_EVENTS = [
    "BlueprintLoaded",
    "ContextRetrieved",
    "VoiceSelected",
    "MusicSelected",
    "PromptComposed",
    "PromptPrepared",
]


@pytest.fixture(scope="module", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=get_engine())


@pytest.fixture
def runtime():
    db = SessionLocal()
    try:
        yield BlueprintRuntime(db)
    finally:
        db.close()


@pytest.mark.parametrize("intention", [*INTENTION_VOICE_MAP.keys(), "default", "not-a-real-slug"])
def test_build_context_for_every_intention(runtime, intention):
    user_id = str(uuid.uuid4())
    ctx = runtime.build_context(user_id, intention)

    assert ctx.user_id == user_id
    assert ctx.intention == intention
    assert ctx.voice_selection is not None
    assert ctx.music_playlist
    assert ctx.prompt_instructions is not None
    assert ctx.composed_prompt is not None
    assert [e.name for e in ctx.events] == EXPECTED_PREP_EVENTS

    expected_voice_id, expected_gender, _ = get_voice_for_intention(intention, None)
    assert ctx.voice_selection.voice_id == expected_voice_id
    assert ctx.voice_selection.gender == expected_gender


def test_build_context_injects_conversation_summary_alongside_brain_context(runtime):
    conv = Conversation(id=str(uuid.uuid4()), summary="The user is winding down after a long week.")
    runtime.db.add(conv)
    runtime.db.commit()

    ctx = runtime.build_context(str(uuid.uuid4()), "peace", conversation_id=conv.id)

    assert "[CONVERSATION SO FAR]" in ctx.brain_context
    assert "winding down after a long week" in ctx.brain_context
    assert "[CONVERSATION SO FAR]" in ctx.prompt_instructions


def test_build_context_without_conversation_id_omits_summary_block(runtime):
    ctx = runtime.build_context(str(uuid.uuid4()), "peace")
    assert "[CONVERSATION SO FAR]" not in ctx.brain_context


def test_empty_slug_blueprint_is_a_hard_validation_issue():
    blueprint = Blueprint(identity={"slug": "", "display_name": "Broken"})
    issues = validate_blueprint(blueprint)
    assert issues == ["identity.slug is empty"]


def test_build_context_falls_back_to_default_on_hard_validation_failure(runtime, monkeypatch):
    broken = Blueprint(identity={"slug": "", "display_name": "Broken"})
    original_load = runtime.blueprint_engine.load

    def fake_load(slug):
        return broken if slug == "ghost" else original_load(slug)

    monkeypatch.setattr(runtime.blueprint_engine, "load", fake_load)

    ctx = runtime.build_context(str(uuid.uuid4()), "ghost")

    assert ctx.blueprint.identity.slug == "default"
    loaded_event = next(e for e in ctx.events if e.name == "BlueprintLoaded")
    assert loaded_event.data["fallback_from"] == "ghost"


def test_unmapped_voice_intention_is_a_soft_warning_only():
    blueprint = Blueprint(
        identity={"slug": "quirky"}, voice_configuration={"voice_intention": "nonexistent"}
    )
    assert validate_blueprint(blueprint) == []
    warnings = blueprint_warnings(blueprint)
    assert any("nonexistent" in w for w in warnings)


def test_unmapped_ambience_key_is_a_soft_warning_only():
    blueprint = Blueprint(
        identity={"slug": "quirky"},
        background_music_strategy={"tone_ambience_key": "nonexistent-tone"},
    )
    assert validate_blueprint(blueprint) == []
    warnings = blueprint_warnings(blueprint)
    assert any("nonexistent-tone" in w for w in warnings)


def _canned_profile() -> EmotionProfile:
    return EmotionProfile(
        tone=EmotionalTone.CALM,
        narration_style=NarrationStyle.FRIEND,
        pacing=Pacing.MEDIUM,
        experience_title="Test",
        voice_id="voice-123",
        voice_name="Test Voice",
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.3),
        ambience_prompt="soft ambient",
        ambience_volume_db=-14.0,
        music_category="calm",
        script="Hello there.",
    )


@pytest.mark.asyncio
async def test_execute_runs_full_lifecycle_and_emits_all_events(runtime, monkeypatch):
    profile = _canned_profile()
    mock_run_pipeline = AsyncMock(return_value=(profile, "/tmp/fake.mp3", 3.2))
    monkeypatch.setattr("app.experience_os.runtime.run_pipeline", mock_run_pipeline)

    experience = await runtime.execute(str(uuid.uuid4()), "I need some peace", intention="peace")

    mock_run_pipeline.assert_awaited_once()
    assert experience.audio_path == "/tmp/fake.mp3"
    assert experience.duration_seconds == 3.2
    assert experience.profile is profile

    call_kwargs = mock_run_pipeline.call_args.kwargs
    assert call_kwargs["composed_prompt"] is experience.context.composed_prompt
    assert call_kwargs["pause_behaviour_enabled"] is True
    assert call_kwargs["pause_behaviour_enabled"] == (
        experience.context.blueprint.pause_behaviour.enabled
    )

    event_names = [e.name for e in experience.context.events]
    assert event_names == [
        "BlueprintLoaded", "ContextRetrieved", "VoiceSelected", "MusicSelected",
        "PromptComposed", "PromptPrepared", "SpeechGenerated", "ReflectionUpdated", "MemoryUpdated",
    ]
    memory_event = next(e for e in experience.context.events if e.name == "MemoryUpdated")
    assert memory_event.data["applied"] is False


@pytest.mark.asyncio
async def test_execute_reply_runs_full_lifecycle_and_emits_all_events(runtime, monkeypatch):
    profile = _canned_profile()
    mock_run_chat_pipeline = AsyncMock(return_value=(profile, "/tmp/fake_chat.mp3", 2.1))
    monkeypatch.setattr("app.experience_os.runtime.run_chat_pipeline", mock_run_chat_pipeline)

    experience = await runtime.execute_reply(
        str(uuid.uuid4()),
        user_message="how are you",
        history=[{"role": "user", "content": "hi"}],
        speaking_styles=[],
        gender="female",
        energy_level=2,
        intention="comfort",
    )

    mock_run_chat_pipeline.assert_awaited_once()
    assert experience.audio_path == "/tmp/fake_chat.mp3"

    call_kwargs = mock_run_chat_pipeline.call_args.kwargs
    assert call_kwargs["composed_prompt"] is experience.context.composed_prompt
    assert call_kwargs["pause_behaviour_enabled"] is True
    assert call_kwargs["pause_behaviour_enabled"] == (
        experience.context.blueprint.pause_behaviour.enabled
    )

    event_names = [e.name for e in experience.context.events]
    assert event_names == [
        "BlueprintLoaded", "ContextRetrieved", "VoiceSelected", "MusicSelected",
        "PromptComposed", "PromptPrepared", "SpeechGenerated", "ReflectionUpdated", "MemoryUpdated",
    ]
