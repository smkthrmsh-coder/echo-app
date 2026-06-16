"""VoiceSelectionService — thin wrapper around the existing voice_mapping logic."""

from __future__ import annotations

from app.services.llm.voice_mapping import get_voice_for_intention


class DefaultVoiceSelectionService:
    def select_voice(self, intention: str | None, gender_preference: str | None) -> tuple[str, str]:
        voice_id, gender, _ = get_voice_for_intention(intention, gender_preference)
        return voice_id, gender
