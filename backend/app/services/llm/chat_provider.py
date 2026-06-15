"""
Chat reply generator — produces short spoken replies for conversation mode.
Supports emotional mode: SSML pauses, lower stability, higher expressiveness.
Voice continuity: locked_voice_id/name pins the same voice for the entire conversation.
"""

import json
import re

import anthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.emotion import EmotionalTone, EmotionProfile, NarrationStyle, Pacing, VoiceSettings
from app.services.llm.voice_profiles import get_voice_for_tone

logger = get_logger(__name__)

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

You MUST respond with valid JSON only:
{
  "tone": "one of: energetic | calm | fierce | comforting | melancholic | playful | mysterious | romantic | anxious | hopeful",
  "script": "string — your spoken reply (50-80 words, written to be heard, not read)"
}"""

CHAT_EMOTIONAL_SYSTEM_PROMPT = """You are Echo, a premium AI voice companion. You speak with deep emotional presence — slow, deliberate, felt.

Your replies are SHORT (50-80 words max). You write for the EAR with emphasis and weight. Use natural pauses (shown by "..." or "—"). Start slow and build. Let silence exist.

Style guide:
- Begin with a short, grounding opening sentence (3-7 words)
- Use em-dashes — to signal a breath
- Place key words where they land hard
- No lists, no markdown, pure spoken feeling

You MUST respond with valid JSON only:
{
  "tone": "one of: energetic | calm | fierce | comforting | melancholic | playful | mysterious | romantic | anxious | hopeful",
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


def _apply_emotional_markup(script: str) -> str:
    """Inject ElevenLabs SSML break tags for natural delivery. Applied to TTS only."""
    marked = "<break time='0.8s'/> " + script
    marked = re.sub(r"\. +", ". <break time='0.5s'/> ", marked)
    marked = re.sub(r", +", ", <break time='0.2s'/> ", marked)
    marked = re.sub(r" — ", " <break time='0.4s'/> — <break time='0.2s'/> ", marked)
    marked = re.sub(r"\.\.\. +", "... <break time='0.6s'/> ", marked)
    return marked


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
    ) -> EmotionProfile:
        style_str = ", ".join(speaking_styles) if speaking_styles else "warm and present"
        energy_desc = ["very gentle", "gentle", "balanced", "energetic", "very energetic"][energy_level - 1]
        style_note = f"Speaking style: {style_str}. Energy: {energy_desc}."

        system = CHAT_EMOTIONAL_SYSTEM_PROMPT if emotional_mode else CHAT_SYSTEM_PROMPT

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

        tone_str = data.get("tone", "comforting").lower()
        try:
            tone = EmotionalTone(tone_str)
        except ValueError:
            tone = EmotionalTone.COMFORTING

        # Voice selection — always run to get voice settings, but override ID/name if locked
        persona_id = speaking_styles[0] if speaking_styles else None
        voice = get_voice_for_tone(tone.value, gender, persona_id=persona_id)

        effective_voice_id = locked_voice_id if locked_voice_id else voice.voice_id
        effective_voice_name = locked_voice_name if locked_voice_name else voice.name

        if emotional_mode:
            vs = VoiceSettings(stability=0.20, similarity_boost=0.85, style=0.90, use_speaker_boost=True)
        else:
            vs = VoiceSettings(
                stability=voice.default_stability,
                similarity_boost=voice.default_similarity,
                style=voice.default_style,
                use_speaker_boost=True,
            )

        clean = _clean_script(data.get("script", "I'm here with you."))
        # SSML markup is applied to script for TTS delivery only
        tts_script = _apply_emotional_markup(clean) if emotional_mode else clean

        ambience_prompt = TONE_AMBIENCE.get(tone.value, "soft ambient background, warm and subtle")

        return EmotionProfile(
            tone=tone,
            narration_style=NarrationStyle.FRIEND,
            pacing=Pacing.SLOW if emotional_mode else Pacing.MEDIUM,
            experience_title="",
            voice_id=effective_voice_id,
            voice_name=effective_voice_name,
            voice_settings=vs,
            ambience_prompt=ambience_prompt,
            ambience_volume_db=-14.0,
            music_category=tone.value,
            script=tts_script,
            reasoning="",
        )
