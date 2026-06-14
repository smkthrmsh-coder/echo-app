from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    session_id: str | None = None


class TranscribeResponse(BaseModel):
    text: str
    confidence: float | None = None
    language: str | None = None


class VoiceSettingsOut(BaseModel):
    stability: float
    similarity_boost: float
    style: float
    use_speaker_boost: bool


class EmotionProfileOut(BaseModel):
    tone: str
    narration_style: str
    pacing: str
    experience_title: str
    voice_id: str
    voice_name: str
    voice_settings: VoiceSettingsOut
    ambience_prompt: str
    music_category: str
    script: str
    reasoning: str


class GenerateResponse(BaseModel):
    generation_id: str
    audio_url: str
    emotion_profile: EmotionProfileOut
    duration_seconds: float | None = None
    prompt: str


# --- Conversation / Chat models ---

class CreateConversationRequest(BaseModel):
    initial_prompt: str = Field(..., min_length=3, max_length=1000)
    speaking_styles: list[str] = Field(default_factory=list)
    gender: str = Field(default="female")
    energy_level: int = Field(default=3, ge=1, le=5)
    persona_id: str | None = None       # Echo persona (sofia, marcus, etc.)
    emotion: str | None = None          # Emotion card selected by user
    celebrity_voice_id: str | None = None
    title: str | None = None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    audio_url: str | None = None
    duration_seconds: float | None = None
    voice_name: str
    tone: str
    created_at: str


class ConversationOut(BaseModel):
    id: str
    title: str
    speaking_styles: list[str]
    gender: str
    energy_level: int
    persona_id: str | None = None
    emotion: str | None = None
    is_pinned: bool
    created_at: str
    updated_at: str
    messages: list[MessageOut] = Field(default_factory=list)


class ConversationSummaryOut(BaseModel):
    id: str
    title: str
    preview: str
    message_count: int
    is_pinned: bool
    emotion: str | None = None
    created_at: str
    updated_at: str


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    emotional_mode: bool = Field(default=False)
    celebrity_voice_id: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None
