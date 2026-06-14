"""
Voice profiles — maps tone+persona to ElevenLabs voice IDs.
Internal pipeline use only; public-facing personas live in voice_personas.py.
"""

from dataclasses import dataclass, field

from app.services.llm.voice_personas import PERSONAS, get_persona


@dataclass
class VoiceOption:
    voice_id: str
    name: str
    gender: str
    archetype: str = ""
    best_for: list[str] = field(default_factory=list)
    default_stability: float = 0.5
    default_similarity: float = 0.80
    default_style: float = 0.45


# Build flat pool from all persona candidates for probe-based fallback
VOICE_POOL: list[VoiceOption] = []
_seen: set[str] = set()
for _p in PERSONAS:
    for _vid in _p.voice_candidates:
        if _vid not in _seen:
            _seen.add(_vid)
            VOICE_POOL.append(
                VoiceOption(
                    voice_id=_vid,
                    name=_p.name,
                    gender=_p.gender if _p.gender != "neutral" else "female",
                    archetype=_p.id,
                    default_stability=_p.default_stability,
                    default_similarity=_p.default_similarity,
                    default_style=_p.default_style,
                )
            )

TONE_TO_VOICE_MAP: dict[str, list[str]] = {
    "energetic":  ["alex", "nova", "charlie"],
    "calm":       ["river", "sofia", "marcus"],
    "fierce":     ["alex", "nova", "atlas"],
    "comforting": ["sofia", "luna", "river"],
    "melancholic":["luna", "sofia", "atlas"],
    "playful":    ["charlie", "alex", "sofia"],
    "mysterious": ["atlas", "luna", "marcus"],
    "romantic":   ["sofia", "luna", "marcus"],
    "anxious":    ["river", "sofia", "atlas"],
    "hopeful":    ["nova", "sofia", "marcus"],
}


def get_voice_for_tone(tone: str, gender_preference: str | None = None, persona_id: str | None = None) -> VoiceOption:
    """
    Return a VoiceOption for the given tone. Persona overrides tone-based selection.
    """
    if persona_id:
        persona = get_persona(persona_id)
        if persona.voice_candidates:
            g = persona.gender if persona.gender != "neutral" else "female"
            return VoiceOption(
                voice_id=persona.voice_candidates[0],
                name=persona.name,
                gender=g,
                archetype=persona.id,
                default_stability=persona.default_stability,
                default_similarity=persona.default_similarity,
                default_style=persona.default_style,
            )

    preferred_ids = TONE_TO_VOICE_MAP.get(tone, ["sofia"])
    by_id = {p.id: p for p in PERSONAS}

    for pid in preferred_ids:
        if pid not in by_id:
            continue
        p = by_id[pid]
        p_gender = p.gender if p.gender != "neutral" else "female"
        if gender_preference is None or p_gender == gender_preference:
            if p.voice_candidates:
                return VoiceOption(
                    voice_id=p.voice_candidates[0],
                    name=p.name,
                    gender=p_gender,
                    archetype=p.id,
                    default_stability=p.default_stability,
                    default_similarity=p.default_similarity,
                    default_style=p.default_style,
                )

    # Final fallback: first voice in pool
    return VOICE_POOL[0]
