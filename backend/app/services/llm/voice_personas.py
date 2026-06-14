"""
Echo Voice Personas — 9 named characters users choose from.
Each maps to probed ElevenLabs voices under the hood so the selection
works on any plan. Future custom voices slot in cleanly here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VoicePersona:
    id: str
    name: str
    tagline: str
    description: str
    gender: str  # "female" | "male" | "neutral"
    # ElevenLabs voice IDs to try in order (first accessible one wins via probe)
    voice_candidates: tuple[str, ...]
    # Default voice settings
    default_stability: float = 0.5
    default_similarity: float = 0.80
    default_style: float = 0.45


PERSONAS: list[VoicePersona] = [
    VoicePersona(
        id="sofia",
        name="Sofia",
        tagline="Warm & Nurturing",
        description="Soft, empathetic, and deeply present. Like your most understanding friend.",
        gender="female",
        voice_candidates=("21m00Tcm4TlvDq8ikWAM", "EXAVITQu4vr4xnSDxMaL", "XrExE9yKIg1WjnnlVkGX", "cgSgspJ2msm6clMCkdW9"),
        default_stability=0.60,
        default_similarity=0.82,
        default_style=0.35,
    ),
    VoicePersona(
        id="marcus",
        name="Marcus",
        tagline="Grounded & Steady",
        description="Calm, measured, and reassuring. A voice that keeps you anchored.",
        gender="male",
        voice_candidates=("TX3LPaxmHKxFdv7VOFE1", "ErXwobaYiN019PkySvjV", "TxGEqnHWrfWFTfGW9XjX", "bIHbv24MWmeRgasZH58o"),
        default_stability=0.65,
        default_similarity=0.80,
        default_style=0.30,
    ),
    VoicePersona(
        id="alex",
        name="Alex",
        tagline="Energetic Coach",
        description="High-energy, direct, and action-oriented. Built to fire you up.",
        gender="female",
        voice_candidates=("AZnzlk1XvdvUeBnXmlld", "cgSgspJ2msm6clMCkdW9", "21m00Tcm4TlvDq8ikWAM"),
        default_stability=0.40,
        default_similarity=0.85,
        default_style=0.70,
    ),
    VoicePersona(
        id="luna",
        name="Luna",
        tagline="Gentle Storyteller",
        description="Soft, imaginative, and quietly magical. Takes you somewhere else.",
        gender="female",
        voice_candidates=("EXAVITQu4vr4xnSDxMaL", "XrExE9yKIg1WjnnlVkGX", "pFZP5JQG7iQjIQuC4Bku"),
        default_stability=0.68,
        default_similarity=0.78,
        default_style=0.40,
    ),
    VoicePersona(
        id="james",
        name="James",
        tagline="Professional",
        description="Clear, composed, and authoritative. For when you need to think clearly.",
        gender="male",
        voice_candidates=("JBFqnCBsd6RMkjVDRZzb", "pNInz6obpgDQGcFmaJgB", "flq6f7UD9byGKBbTKkKm"),
        default_stability=0.70,
        default_similarity=0.82,
        default_style=0.25,
    ),
    VoicePersona(
        id="charlie",
        name="Charlie",
        tagline="Friendly",
        description="Casual, upbeat, and easy to talk to. Like a friend who always has time.",
        gender="male",
        voice_candidates=("IKne3meq5aSn9XLyUdCD", "bIHbv24MWmeRgasZH58o", "ErXwobaYiN019PkySvjV"),
        default_stability=0.52,
        default_similarity=0.80,
        default_style=0.50,
    ),
    VoicePersona(
        id="nova",
        name="Nova",
        tagline="Motivational",
        description="Bold, inspiring, and unapologetic. Makes you believe in yourself again.",
        gender="female",
        voice_candidates=("AZnzlk1XvdvUeBnXmlld", "MF3mGyEYCl7XYWbV9V6O", "cgSgspJ2msm6clMCkdW9"),
        default_stability=0.38,
        default_similarity=0.88,
        default_style=0.75,
    ),
    VoicePersona(
        id="river",
        name="River",
        tagline="Calm Companion",
        description="Peaceful, present, and unhurried. Like a slow exhale.",
        gender="female",
        voice_candidates=("piTKgcLEGmPE4e6mEKli", "oWAxZDx7w5VEj9dCyTzz", "pMsXgVXv3BLzUgSXRplE"),
        default_stability=0.75,
        default_similarity=0.78,
        default_style=0.20,
    ),
    VoicePersona(
        id="atlas",
        name="Atlas",
        tagline="Wise Mentor",
        description="Thoughtful, deep, and unhurried. The voice of earned wisdom.",
        gender="male",
        voice_candidates=("ZQe5CZNOzWyzPSCn5a3c", "Zlb1dXrM653N07WRdFW3", "JBFqnCBsd6RMkjVDRZzb"),
        default_stability=0.72,
        default_similarity=0.82,
        default_style=0.30,
    ),
]

PERSONA_MAP: dict[str, VoicePersona] = {p.id: p for p in PERSONAS}


def get_persona(persona_id: str) -> VoicePersona:
    return PERSONA_MAP.get(persona_id, PERSONAS[0])


def get_persona_for_gender(gender: str) -> VoicePersona:
    """Return a sensible default persona for a given gender preference."""
    defaults = {"female": "sofia", "male": "marcus", "neutral": "river"}
    return PERSONA_MAP[defaults.get(gender, "sofia")]


def persona_voice_ids(persona: VoicePersona) -> list[str]:
    return list(persona.voice_candidates)
