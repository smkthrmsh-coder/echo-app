import json
import re

import anthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.emotion import (
    EmotionalTone,
    EmotionProfile,
    NarrationStyle,
    Pacing,
    VoiceSettings,
)
from app.services.llm.base import LLMProvider
from app.services.llm.voice_profiles import get_voice_for_tone

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert AI emotion director and voice experience designer.

Given a user's emotional request, you must:
1. Deeply understand the emotional need behind the prompt
2. Design a complete emotional audio experience
3. Write an immersive narration script (150-250 words)

You MUST respond with valid JSON only. No markdown, no explanation outside the JSON.

JSON schema:
{
  "experience_title": "string — evocative title (3-6 words)",
  "tone": "one of: energetic | calm | fierce | comforting | melancholic | playful | mysterious | romantic | anxious | hopeful",
  "narration_style": "one of: coach | narrator | whisper | storyteller | friend | guide",
  "pacing": "one of: fast | medium | slow | very_slow",
  "gender_preference": "male | female | null",
  "stability": "float 0.0-1.0 (lower = more emotional variation, higher = more consistent)",
  "similarity_boost": "float 0.0-1.0",
  "style": "float 0.0-1.0 (higher = more expressive delivery)",
  "use_speaker_boost": "boolean",
  "ambience_prompt": "string — detailed sound design prompt for ElevenLabs Sound Effects API (20-40 words, describe specific sounds, textures, environment)",
  "ambience_volume_db": "float — relative volume of ambience vs voice. Range: -30 to -8. Use -20 for subtle, -12 for present, -8 for immersive",
  "music_category": "string — brief category label (e.g. cinematic, ambient, nature, electronic, orchestral, lo-fi)",
  "script": "string — the full narration script (150-250 words, immersive, emotionally intelligent, written for spoken delivery with natural pauses)",
  "reasoning": "string — brief explanation of your emotional design choices (1-2 sentences)"
}

Script writing guidelines:
- Write for the EAR, not the eye
- Use natural spoken rhythms, contractions, pauses implied by punctuation
- Be emotionally present — speak TO the listener, not AT them
- Match energy to tone: fierce=short punchy sentences, calm=flowing long sentences
- Include sensory details that anchor the emotional experience
- End with emotional resolution or momentum"""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature

    async def analyze_and_generate(self, prompt: str) -> EmotionProfile:
        logger.info(f"Analyzing prompt: {prompt!r}")

        user_message = f'User emotional request: "{prompt}"\n\nDesign the complete emotional audio experience and write the narration script.'

        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = message.content[0].text
        logger.debug(f"LLM raw response: {raw[:200]}...")

        data = _extract_json(raw)
        return self._build_profile(data)

    def _build_profile(self, data: dict) -> EmotionProfile:
        tone_str = data.get("tone", "calm").lower()
        try:
            tone = EmotionalTone(tone_str)
        except ValueError:
            tone = EmotionalTone.CALM

        narration_str = data.get("narration_style", "narrator").lower()
        try:
            narration_style = NarrationStyle(narration_str)
        except ValueError:
            narration_style = NarrationStyle.NARRATOR

        pacing_str = data.get("pacing", "medium").lower()
        try:
            pacing = Pacing(pacing_str)
        except ValueError:
            pacing = Pacing.MEDIUM

        gender_pref = data.get("gender_preference")
        voice = get_voice_for_tone(tone.value, gender_pref)

        # LLM can override voice settings; clamp to valid range
        def clamp(v, lo=0.0, hi=1.0):
            return max(lo, min(hi, float(v)))

        voice_settings = VoiceSettings(
            stability=clamp(data.get("stability", voice.default_stability)),
            similarity_boost=clamp(data.get("similarity_boost", voice.default_similarity)),
            style=clamp(data.get("style", voice.default_style)),
            use_speaker_boost=bool(data.get("use_speaker_boost", True)),
        )

        ambience_vol = float(data.get("ambience_volume_db", -18.0))
        ambience_vol = max(-30.0, min(-8.0, ambience_vol))

        return EmotionProfile(
            tone=tone,
            narration_style=narration_style,
            pacing=pacing,
            experience_title=data.get("experience_title", "Emotional Journey"),
            voice_id=voice.voice_id,
            voice_name=voice.name,
            voice_settings=voice_settings,
            ambience_prompt=data.get("ambience_prompt", "soft ambient background"),
            ambience_volume_db=ambience_vol,
            music_category=data.get("music_category", "ambient"),
            script=data.get("script", ""),
            reasoning=data.get("reasoning", ""),
        )
