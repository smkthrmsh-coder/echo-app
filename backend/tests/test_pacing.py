"""Tests for the shared SSML pause-pacing markup used by both LLM providers."""

from app.services.llm.pacing import DEFAULT_PACING, INTENTION_PACING, apply_pacing_markup


def test_peace_has_a_long_reflective_ellipsis_pause():
    assert INTENTION_PACING["peace"]["ellipsis"] == "3.2s"


def test_apply_pacing_markup_uses_intention_specific_pacing():
    marked = apply_pacing_markup("Hello... I hear you.", intention="peace")
    assert "<break time='3.2s'/>" in marked
    assert f"<break time='{INTENTION_PACING['peace']['open']}'/>" in marked


def test_apply_pacing_markup_falls_back_to_default_for_unknown_intention():
    marked = apply_pacing_markup("Hello... there.", intention="not-a-real-intention")
    assert f"<break time='{DEFAULT_PACING['ellipsis']}'/>" in marked


def test_apply_pacing_markup_falls_back_to_default_for_none_intention():
    marked = apply_pacing_markup("Hello, friend.", intention=None)
    assert f"<break time='{DEFAULT_PACING['comma']}'/>" in marked


def _seconds(intention: str, key: str) -> float:
    return float(INTENTION_PACING[intention][key].rstrip("s"))


def test_sleep_exceeds_peace_on_every_pacing_axis():
    for key in ("open", "sentence", "comma", "em", "ellipsis"):
        assert _seconds("sleep", key) > _seconds("peace", key), key


def test_energy_is_the_fastest_of_all_nine_v1_intentions():
    v1_intentions = [
        "peace", "motivation", "confidence", "comfort", "sleep",
        "focus", "clarity", "energy", "encouragement",
    ]
    for key in ("open", "sentence", "comma", "em", "ellipsis"):
        energy_value = _seconds("energy", key)
        for intention in v1_intentions:
            if intention == "energy":
                continue
            assert energy_value < _seconds(intention, key), (intention, key)


def test_clarity_exceeds_focus_on_every_pacing_axis():
    for key in ("open", "sentence", "comma", "em", "ellipsis"):
        assert _seconds("clarity", key) > _seconds("focus", key), key


def test_encouragement_exceeds_confidence_on_every_pacing_axis():
    for key in ("open", "sentence", "comma", "em", "ellipsis"):
        assert _seconds("encouragement", key) > _seconds("confidence", key), key
