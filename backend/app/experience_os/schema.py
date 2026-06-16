"""
Blueprint schema — the structured configuration that will eventually drive every
emotional experience (voice, prompt, retrieval, journey, music, reflection, ...).

This sprint defines the schema only. Every section ships with safe defaults so a
near-empty placeholder Blueprint YAML validates. No section is read by real
behaviour yet except VoiceConfiguration's resolved fields (see blueprint_engine.py).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Identity(BaseModel):
    slug: str
    display_name: str = ""
    category: str = ""


class EmotionalObjective(BaseModel):
    primary_goal: str = ""
    secondary_goals: list[str] = Field(default_factory=list)


class PromptInstructions(BaseModel):
    base_prompt_override: str | None = None
    style_notes: list[str] = Field(default_factory=list)


class RetrievalStrategy(BaseModel):
    use_universal_memory: bool = True
    use_experience_memory: bool = False
    use_session_memory: bool = False


class ContextVerification(BaseModel):
    enabled: bool = False
    rules: list[str] = Field(default_factory=list)


class JourneyStrategy(BaseModel):
    enabled: bool = False
    journey_slug: str | None = None


class VoiceConfiguration(BaseModel):
    # Source field — a key into the existing INTENTION_VOICE_MAP. Never hardcode IDs here.
    voice_intention: str = "comfort"
    default_gender: str | None = None
    # Resolved at load time by BlueprintEngine from voice_mapping.py — not set in YAML.
    resolved_male_voice_id: str | None = None
    resolved_female_voice_id: str | None = None
    resolved_stability: float | None = None
    resolved_similarity_boost: float | None = None
    resolved_style: float | None = None
    voice_continuity_rules: str = "lock voice for the conversation once selected"


class SpeechBehaviour(BaseModel):
    pacing: str = "medium"
    warmth: str = "warm"
    energy: str = "balanced"
    fillers_allowed: bool = False


class PauseBehaviour(BaseModel):
    enabled: bool = False
    pause_style: str | None = None


class VocabularyStyle(BaseModel):
    tone_words: list[str] = Field(default_factory=list)


class SentenceStructure(BaseModel):
    style: str = "natural"


class BackgroundMusicStrategy(BaseModel):
    tone_ambience_key: str | None = None
    category: str = ""


class ReflectionRules(BaseModel):
    enabled: bool = False
    frequency: str | None = None


class MemoryUpdateRules(BaseModel):
    enabled: bool = True
    categories: list[str] = Field(default_factory=list)


class UIBehaviour(BaseModel):
    theme_color: str | None = None
    icon: str | None = None
    notes: str = ""


class Analytics(BaseModel):
    tags: list[str] = Field(default_factory=list)


class Blueprint(BaseModel):
    identity: Identity
    emotional_objective: EmotionalObjective = Field(default_factory=EmotionalObjective)
    prompt_instructions: PromptInstructions = Field(default_factory=PromptInstructions)
    retrieval_strategy: RetrievalStrategy = Field(default_factory=RetrievalStrategy)
    context_verification: ContextVerification = Field(default_factory=ContextVerification)
    journey_strategy: JourneyStrategy = Field(default_factory=JourneyStrategy)
    voice_configuration: VoiceConfiguration = Field(default_factory=VoiceConfiguration)
    speech_behaviour: SpeechBehaviour = Field(default_factory=SpeechBehaviour)
    pause_behaviour: PauseBehaviour = Field(default_factory=PauseBehaviour)
    vocabulary_style: VocabularyStyle = Field(default_factory=VocabularyStyle)
    sentence_structure: SentenceStructure = Field(default_factory=SentenceStructure)
    background_music_strategy: BackgroundMusicStrategy = Field(
        default_factory=BackgroundMusicStrategy
    )
    reflection_rules: ReflectionRules = Field(default_factory=ReflectionRules)
    memory_update_rules: MemoryUpdateRules = Field(default_factory=MemoryUpdateRules)
    ui_behaviour: UIBehaviour = Field(default_factory=UIBehaviour)
    analytics: Analytics = Field(default_factory=Analytics)
