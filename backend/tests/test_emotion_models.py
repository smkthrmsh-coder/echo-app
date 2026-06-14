"""Tests for emotion models and voice profile mapping."""


from app.models.emotion import (
    EmotionalTone,
    EmotionProfile,
    NarrationStyle,
    Pacing,
    VoiceSettings,
)
from app.services.llm.voice_profiles import (
    TONE_TO_VOICE_MAP,
    VOICE_POOL,
    get_voice_for_tone,
)


def test_all_tones_have_voice_mapping():
    for tone in EmotionalTone:
        assert tone.value in TONE_TO_VOICE_MAP, f"No voice mapping for tone: {tone.value}"


def test_get_voice_for_tone_returns_valid_voice():
    for tone in EmotionalTone:
        voice = get_voice_for_tone(tone.value)
        assert voice.voice_id, f"Empty voice_id for tone {tone.value}"
        assert voice.name, f"Empty voice name for tone {tone.value}"
        assert 0.0 <= voice.default_stability <= 1.0
        assert 0.0 <= voice.default_similarity <= 1.0
        assert 0.0 <= voice.default_style <= 1.0


def test_get_voice_gender_preference_female():
    voice = get_voice_for_tone("energetic", gender_preference="female")
    assert voice.gender == "female"


def test_get_voice_gender_preference_male():
    voice = get_voice_for_tone("calm", gender_preference="male")
    assert voice.gender == "male"


def test_get_voice_unknown_tone_fallback():
    voice = get_voice_for_tone("nonexistent_tone")
    assert voice is not None


def test_emotion_profile_defaults():
    profile = EmotionProfile()
    assert profile.tone == EmotionalTone.CALM
    assert profile.pacing == Pacing.MEDIUM
    assert profile.narration_style == NarrationStyle.NARRATOR
    assert profile.voice_settings.stability == 0.5


def test_voice_settings_range():
    vs = VoiceSettings(stability=0.9, similarity_boost=0.1, style=1.0)
    assert vs.stability == 0.9
    assert vs.similarity_boost == 0.1
    assert vs.style == 1.0


def test_voice_pool_completeness():
    names = {v.name for v in VOICE_POOL}
    assert len(names) == len(VOICE_POOL), "Duplicate names in voice pool"
    for v in VOICE_POOL:
        assert len(v.voice_id) > 10, f"Suspicious short voice_id for {v.name}"
        assert len(v.best_for) >= 1
