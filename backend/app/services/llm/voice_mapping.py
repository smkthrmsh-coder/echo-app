"""
Voice Selection Engine — maps emotional intention × gender to ElevenLabs voice IDs.

All voice IDs live here. Never hardcode them elsewhere in the application.
To add or change a voice, update only this file.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class IntentionVoice:
    male_id: str
    female_id: str
    # ElevenLabs voice settings tuned for the emotional context
    stability: float        # lower = more expressive variation; higher = more consistent
    similarity_boost: float
    style: float            # higher = more dramatic, conviction-driven delivery
    speech_rate: float = 1.0  # ElevenLabs speed multiplier: 0.7 (slowest) → 1.3 (fastest)


# Intention key → voice IDs and delivery settings
# Keys match the IntentionId values from the frontend (INTENTIONS const)
INTENTION_VOICE_MAP: dict[str, IntentionVoice] = {
    "peace": IntentionVoice(
        male_id="NcJuO1kJ19MefFnxN1Ls",
        female_id="d5QfMetkf8n1aenR1dOq",
        stability=0.65, similarity_boost=0.75, style=0.20, speech_rate=0.88,
    ),
    "confidence": IntentionVoice(
        male_id="Pcfg2Zc6kmNWQ9ji3J5F",
        female_id="YgzytRZyVmEux6PCtJYB",
        stability=0.32, similarity_boost=0.75, style=0.78, speech_rate=1.15,
    ),
    "motivation": IntentionVoice(
        male_id="XALcFq0WF65uNKzmpcZW",
        female_id="cvpTJfe9LINpHIOmB2Hp",
        stability=0.28, similarity_boost=0.75, style=0.82, speech_rate=1.20,
    ),
    "comfort": IntentionVoice(
        male_id="vSjOBQp24DUB2COr2xI9",
        female_id="WyFXw4PzMbRnp8iLMJwY",
        stability=0.52, similarity_boost=0.78, style=0.45, speech_rate=0.92,
    ),
    "focus": IntentionVoice(
        male_id="3eeW5idatACfmf9haBcH",
        female_id="OYTbf65OHHFELVut7v2H",
        stability=0.55, similarity_boost=0.75, style=0.35, speech_rate=1.02,
    ),
    "sleep": IntentionVoice(
        male_id="KH1SQLVulwP6uG4O3nmT",
        female_id="tdOAypddKoCTtFZLeKO2",
        stability=0.68, similarity_boost=0.75, style=0.18, speech_rate=0.80,
    ),
    "energy": IntentionVoice(
        male_id="UgBBYS2sOqTuMpoF3BR0",
        female_id="cvpTJfe9LINpHIOmB2Hp",
        stability=0.28, similarity_boost=0.75, style=0.82, speech_rate=1.22,
    ),
    "clarity": IntentionVoice(
        male_id="ZoiZ8fuDWlnAcwPXaVeq",
        female_id="xYa75LlayhWHCRl1yJSH",
        stability=0.55, similarity_boost=0.75, style=0.32, speech_rate=1.02,
    ),
    "encouragement": IntentionVoice(
        male_id="inGcvmoPgbvKUk9uCvHu",
        female_id="y2TOWGCXSYEgBanvKsYJ",
        stability=0.42, similarity_boost=0.75, style=0.62, speech_rate=1.08,
    ),
    "listen": IntentionVoice(
        male_id="EAFdcgh6sHQjl7oc0rRa",
        female_id="BNmqhlQbvg4uYNDVazX",
        stability=0.55, similarity_boost=0.78, style=0.40, speech_rate=1.0,
    ),
}

# When user picks "Auto", Echo intelligently selects gender per intention
_AUTO_GENDER: dict[str, str] = {
    "peace": "female",
    "confidence": "male",
    "motivation": "male",
    "comfort": "female",
    "focus": "male",
    "sleep": "female",
    "energy": "male",
    "clarity": "female",
    "encouragement": "male",
    "listen": "female",
    "other": "female",
}

_DEFAULT = INTENTION_VOICE_MAP["comfort"]


def get_voice_for_intention(
    intention: str | None,
    gender_preference: str | None,
) -> tuple[str, str, IntentionVoice]:
    """
    Returns (voice_id, resolved_gender, intention_voice).

    intention: the user's selected emotional intention (e.g. "comfort", "focus")
    gender_preference: "male" | "female" | "auto" | None
    """
    key = (intention or "comfort").lower()
    mapping = INTENTION_VOICE_MAP.get(key, _DEFAULT)

    if gender_preference and gender_preference not in ("auto", ""):
        gender = gender_preference
    else:
        gender = _AUTO_GENDER.get(key, "female")

    voice_id = mapping.male_id if gender == "male" else mapping.female_id
    return voice_id, gender, mapping
