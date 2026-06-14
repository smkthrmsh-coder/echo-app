"""Tests for LLM response parsing — runs without real API calls."""

import pytest

from app.services.llm.anthropic_provider import AnthropicProvider, _extract_json


def test_extract_json_plain():
    raw = '{"tone": "calm", "script": "Hello world"}'
    data = _extract_json(raw)
    assert data["tone"] == "calm"


def test_extract_json_with_markdown_fence():
    raw = '```json\n{"tone": "energetic"}\n```'
    data = _extract_json(raw)
    assert data["tone"] == "energetic"


def test_extract_json_with_plain_fence():
    raw = '```\n{"tone": "fierce"}\n```'
    data = _extract_json(raw)
    assert data["tone"] == "fierce"


def test_extract_json_invalid_raises():
    with pytest.raises(Exception):
        _extract_json("not json at all")


def test_build_profile_minimal(monkeypatch):
    """_build_profile works with minimal data, falling back gracefully."""
    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    monkeypatch.setenv("LLM_MODEL", "claude-sonnet-4-6")

    # Bypass actual Anthropic client init
    from unittest.mock import MagicMock

    original_client = anthropic.Anthropic

    try:
        anthropic.Anthropic = MagicMock(return_value=MagicMock())
        provider = AnthropicProvider()
        profile = provider._build_profile({
            "tone": "energetic",
            "narration_style": "coach",
            "pacing": "fast",
            "experience_title": "Test Experience",
            "stability": 0.3,
            "similarity_boost": 0.8,
            "style": 0.7,
            "use_speaker_boost": True,
            "ambience_prompt": "gym sounds",
            "ambience_volume_db": -15,
            "music_category": "cinematic",
            "script": "Let's go!",
            "reasoning": "High energy required.",
        })
        from app.models.emotion import EmotionalTone, NarrationStyle, Pacing
        assert profile.tone == EmotionalTone.ENERGETIC
        assert profile.pacing == Pacing.FAST
        assert profile.narration_style == NarrationStyle.COACH
        assert profile.script == "Let's go!"
        assert profile.voice_id  # should have a real voice ID
        assert -30 <= profile.ambience_volume_db <= -8
    finally:
        anthropic.Anthropic = original_client


def test_build_profile_unknown_tone_fallback(monkeypatch):
    """Unknown tone values fall back to CALM."""
    from unittest.mock import MagicMock

    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    original = anthropic.Anthropic
    try:
        anthropic.Anthropic = MagicMock(return_value=MagicMock())
        from app.services.llm.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider()
        profile = provider._build_profile({"tone": "TOTALLY_UNKNOWN"})
        from app.models.emotion import EmotionalTone
        assert profile.tone == EmotionalTone.CALM
    finally:
        anthropic.Anthropic = original


def test_ambience_volume_clamped(monkeypatch):
    """ambience_volume_db is clamped to [-30, -8]."""
    from unittest.mock import MagicMock

    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    original = anthropic.Anthropic
    try:
        anthropic.Anthropic = MagicMock(return_value=MagicMock())
        from app.services.llm.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider()
        profile_low = provider._build_profile({"ambience_volume_db": -100})
        assert profile_low.ambience_volume_db == -30.0
        profile_high = provider._build_profile({"ambience_volume_db": 0})
        assert profile_high.ambience_volume_db == -8.0
    finally:
        anthropic.Anthropic = original
