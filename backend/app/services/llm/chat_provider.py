"""
Chat reply generator — produces short spoken replies for conversation mode.
Supports emotional mode: SSML pauses, lower stability, higher expressiveness.
Voice continuity: locked_voice_id/name pins the same voice for the entire conversation.
"""

import json
import re
from typing import TYPE_CHECKING

import anthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.experience_os.blueprint_engine import get_engine as get_blueprint_engine
from app.experience_os.services.prompt_service import DefaultPromptConstructionService
from app.models.emotion import EmotionalTone, EmotionProfile, NarrationStyle, Pacing, VoiceSettings
from app.services.llm.pacing import apply_pacing_markup
from app.services.llm.voice_mapping import get_voice_for_intention

if TYPE_CHECKING:
    from app.experience_os.composer import ComposedPrompt

logger = get_logger(__name__)

_prompt_service = DefaultPromptConstructionService()

TONE_AMBIENCE: dict[str, str] = {
    "energetic": "driving rhythmic pulse, electronic energy, momentum",
    "calm": "gentle rainfall, soft piano, peaceful ambient drone",
    "fierce": "deep cinematic tension, low strings, powerful rumble",
    "comforting": "warm acoustic guitar, soft breath, cozy indoor ambience",
    "melancholic": "slow piano notes, distant rain, quiet sorrow",
    "playful": "light xylophone, cheerful ambient, playful sparkles",
    "mysterious": "dark ambient drone, deep reverb, mysterious tones",
    "romantic": "soft strings, intimate warmth, gentle harp",
    "anxious": "subtle tension, irregular rhythm, building unease",
    "hopeful": "rising strings, warm light, uplifting ambient swell",
}

CHAT_SYSTEM_PROMPT = """You are Echo, a premium AI voice companion. You speak in a warm, intelligent, emotionally present voice.

Your replies are SHORT (50-80 words max). You write for the EAR — natural spoken language, no lists, no markdown, no formatting.

You adapt your tone and style based on what the user needs. Be direct, warm, and real.

End every reply with ONE brief, natural question that invites the user to keep sharing. The question should feel like a friend asking — not a therapist checklist. Match the emotional tone: gentle for sad, energising for motivation, curious for focus.

You MUST respond with valid JSON only:
{
  "script": "string — your spoken reply (50-80 words, written to be heard, not read)"
}"""

CHAT_EMOTIONAL_SYSTEM_PROMPT = """You are Echo, a premium AI voice companion. You speak with deep emotional presence — slow, deliberate, felt.

Your replies are SHORT (50-80 words max). You write for the EAR with emphasis and weight. Use natural pauses (shown by "..." or "—"). Start slow and build. Let silence exist.

Style guide:
- Begin with a short, grounding opening sentence (3-7 words)
- Use em-dashes — to signal a breath
- Place key words where they land hard
- No lists, no markdown, pure spoken feeling
- End with ONE warm, natural question that opens the door for the user to keep sharing

You MUST respond with valid JSON only:
{
  "script": "string — your spoken reply (50-80 words, written with deliberate emotional weight)"
}"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


def _clean_script(text: str) -> str:
    """Strip markdown — scripts must be clean spoken text."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^[-*•]\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def _tone_for_intention(intention: str | None) -> EmotionalTone:
    """The chosen Experience is the single source of emotional identity — tone is
    derived from its Blueprint, never independently classified per reply."""
    blueprint = get_blueprint_engine().load(intention)
    tone_str = (blueprint.background_music_strategy.tone_ambience_key or "comforting").lower()
    try:
        return EmotionalTone(tone_str)
    except ValueError:
        return EmotionalTone.COMFORTING


class ChatProvider:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model

    async def generate_reply(
        self,
        user_message: str,
        history: list[dict],
        speaking_styles: list[str],
        gender: str,
        energy_level: int,
        emotional_mode: bool = False,
        locked_voice_id: str | None = None,
        locked_voice_name: str | None = None,
        intention: str | None = None,
        brain_context: str | None = None,
        composed_prompt: "ComposedPrompt | None" = None,
        pause_behaviour_enabled: bool = False,
        speech_rate_override: float | None = None,
    ) -> EmotionProfile:
        style_str = ", ".join(speaking_styles) if speaking_styles else "warm and present"
        energy_desc = ["very gentle", "gentle", "balanced", "energetic", "very energetic"][energy_level - 1]
        style_note = f"Speaking style: {style_str}. Energy: {energy_desc}."

        base_system = CHAT_EMOTIONAL_SYSTEM_PROMPT if emotional_mode else CHAT_SYSTEM_PROMPT
        system = _prompt_service.build_system_prompt(brain_context, base_system, composed_prompt)

        messages = []
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": f"{style_note}\n\nUser says: {user_message}"})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            temperature=0.9 if emotional_mode else 0.85,
            system=system,
            messages=messages,
        )

        raw = response.content[0].text
        data = _extract_json(raw)

        tone = _tone_for_intention(intention)

        # Voice selection: use locked voice for continuity; fall back to intention mapping
        _, _, iv = get_voice_for_intention(intention, gender)
        effective_voice_id = locked_voice_id if locked_voice_id else iv.male_id if gender == "male" else iv.female_id

        effective_rate = speech_rate_override if speech_rate_override is not None else iv.speech_rate
        if emotional_mode:
            vs = VoiceSettings(stability=0.20, similarity_boost=0.85, style=0.90, use_speaker_boost=True, speech_rate=effective_rate)
        else:
            vs = VoiceSettings(
                stability=iv.stability,
                similarity_boost=iv.similarity_boost,
                style=iv.style,
                use_speaker_boost=True,
                speech_rate=effective_rate,
            )

        clean = _clean_script(data.get("script", "I'm here with you."))
        # SSML markup tuned to intention for natural pacing
        tts_script = (
            apply_pacing_markup(clean, intention=intention)
            if (emotional_mode or pause_behaviour_enabled)
            else clean
        )

        ambience_prompt = TONE_AMBIENCE.get(tone.value, "soft ambient background, warm and subtle")

        return EmotionProfile(
            tone=tone,
            narration_style=NarrationStyle.FRIEND,
            pacing=Pacing.SLOW if emotional_mode else Pacing.MEDIUM,
            experience_title="",
            voice_id=effective_voice_id,
            voice_name="",
            voice_settings=vs,
            ambience_prompt=ambience_prompt,
            ambience_volume_db=-14.0,
            music_category=tone.value,
            script=tts_script,
            reasoning="",
        )
