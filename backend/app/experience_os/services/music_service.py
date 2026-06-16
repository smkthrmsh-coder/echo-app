"""MusicSelectionService — thin wrapper around the existing TONE_AMBIENCE lookup."""

from __future__ import annotations

from app.services.llm.chat_provider import TONE_AMBIENCE

_FALLBACK = "soft ambient background, warm and subtle"


class DefaultMusicSelectionService:
    def select_ambience(self, tone: str) -> str:
        return TONE_AMBIENCE.get(tone, _FALLBACK)
