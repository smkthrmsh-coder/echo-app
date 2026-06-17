from dataclasses import dataclass, field
from enum import StrEnum


class EmotionalTone(StrEnum):
    ENERGETIC = "energetic"
    CALM = "calm"
    FIERCE = "fierce"
    COMFORTING = "comforting"
    MELANCHOLIC = "melancholic"
    PLAYFUL = "playful"
    MYSTERIOUS = "mysterious"
    ROMANTIC = "romantic"
    ANXIOUS = "anxious"
    HOPEFUL = "hopeful"


class Pacing(StrEnum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    VERY_SLOW = "very_slow"


class NarrationStyle(StrEnum):
    COACH = "coach"
    NARRATOR = "narrator"
    WHISPER = "whisper"
    STORYTELLER = "storyteller"
    FRIEND = "friend"
    GUIDE = "guide"


@dataclass
class VoiceSettings:
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.5
    use_speaker_boost: bool = True
    speech_rate: float = 1.0  # ElevenLabs speed: 0.7 (slow) → 1.3 (fast)


@dataclass
class EmotionProfile:
    # Emotional character
    tone: EmotionalTone = EmotionalTone.CALM
    narration_style: NarrationStyle = NarrationStyle.NARRATOR
    pacing: Pacing = Pacing.MEDIUM
    experience_title: str = ""

    # ElevenLabs voice
    voice_id: str = ""
    voice_name: str = ""
    voice_settings: VoiceSettings = field(default_factory=VoiceSettings)

    # Ambience
    ambience_prompt: str = ""
    ambience_volume_db: float = -18.0
    music_category: str = "ambient"

    # Generated narration script
    script: str = ""

    # Reasoning from LLM (for transparency)
    reasoning: str = ""
