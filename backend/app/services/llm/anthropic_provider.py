import json
import re
from typing import TYPE_CHECKING

import anthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.experience_os.services.prompt_service import DefaultPromptConstructionService
from app.models.emotion import (
    EmotionalTone,
    EmotionProfile,
    NarrationStyle,
    Pacing,
    VoiceSettings,
)
from app.services.llm.base import LLMProvider
from app.services.llm.voice_mapping import get_voice_for_intention

if TYPE_CHECKING:
    from app.experience_os.composer import ComposedPrompt

logger = get_logger(__name__)

_prompt_service = DefaultPromptConstructionService()

SYSTEM_PROMPT = """You are Echo, a warm AI voice companion and emotion director.

Given a user's emotional request, you must:
1. Deeply understand the emotional need behind the prompt
2. Design a complete emotional audio experience
3. Write a concise, personal narration script (60-90 words)

CRITICAL: Always open with a warm personal greeting using the user's name. Match it to the emotion:
- Comforting / peace / sleep / grief / listen → "Hey {name}, I hear you."
- Confidence / motivation / energy / encouragement → "Hey {name}, you came to the right place."
- Focus / clarity / productivity → "Hey {name}, let's get you there."
- Default / other → "Hey {name}, I'm glad you're here."

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
  "script": "string — the narration script (60-90 words, immersive, emotionally intelligent, written for spoken delivery)",
  "reasoning": "string — brief explanation of your emotional design choices (1-2 sentences)"
}

Script writing guidelines:
- Write for the EAR, not the eye — short, punchy, spoken
- Be emotionally present — speak TO the listener, not AT them
- Match energy to tone: fierce=short punchy sentences, calm=flowing sentences
- End with ONE brief, natural question that invites the user to share more — match the energy of the tone (gentle for peace/comfort, energising for motivation/confidence)"""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


def _clean_script(text: str) -> str:
    """Strip markdown formatting — scripts must be clean spoken text."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^[-*•]\s+', '', text, flags=re.MULTILINE)
    return text.strip()


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature

    async def analyze_and_generate(
        self,
        prompt: str,
        user_gender: str | None = None,
        user_styles: list[str] | None = None,
        username: str = "there",
        intention: str | None = None,
        brain_context: str | None = None,
        composed_prompt: "ComposedPrompt | None" = None,
    ) -> EmotionProfile:
        logger.info(f"Analyzing prompt: {prompt!r}")

        style_note = ""
        if user_styles:
            style_map = {
                "calm": "calm and gentle", "friendly": "warm and friendly",
                "direct": "direct and clear", "mentor": "wise and mentoring",
                "coach": "motivational coaching", "gentle": "soft and gentle",
                "funny": "light and humorous",
            }
            style_desc = style_map.get(user_styles[0], user_styles[0])
            style_note = f" Write in a {style_desc} style."

        user_message = (
            f'User name: {username}. User emotional request: "{prompt}".'
            f'{style_note}'
            f'\n\nDesign the complete emotional audio experience and write the narration script. '
            f'Open with a warm greeting using "{username}" as instructed.'
        )

        system = _prompt_service.build_system_prompt(brain_context, SYSTEM_PROMPT, composed_prompt)
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = message.content[0].text
        logger.debug(f"LLM raw response: {raw[:200]}...")

        data = _extract_json(raw)
        return self._build_profile(data, user_gender=user_gender, intention=intention)

    def _build_profile(self, data: dict, user_gender: str | None = None, intention: str | None = None) -> EmotionProfile:
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

        # Deterministic voice selection: intention × gender → specific voice ID
        voice_id, _, iv = get_voice_for_intention(intention, user_gender)

        def clamp(v, lo=0.0, hi=1.0):
            return max(lo, min(hi, float(v)))

        voice_settings = VoiceSettings(
            stability=clamp(data.get("stability", iv.stability)),
            similarity_boost=clamp(data.get("similarity_boost", iv.similarity_boost)),
            style=clamp(data.get("style", iv.style)),
            use_speaker_boost=bool(data.get("use_speaker_boost", True)),
        )

        ambience_vol = float(data.get("ambience_volume_db", -18.0))
        ambience_vol = max(-30.0, min(-8.0, ambience_vol))

        return EmotionProfile(
            tone=tone,
            narration_style=narration_style,
            pacing=pacing,
            experience_title=data.get("experience_title", "Emotional Journey"),
            voice_id=voice_id,
            voice_name="",
            voice_settings=voice_settings,
            ambience_prompt=data.get("ambience_prompt", "soft ambient background"),
            ambience_volume_db=ambience_vol,
            music_category=data.get("music_category", "ambient"),
            script=_clean_script(data.get("script", "")),
            reasoning=data.get("reasoning", ""),
        )
