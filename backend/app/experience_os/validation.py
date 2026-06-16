"""
Blueprint validation for BlueprintRuntime.

Two severity tiers:
- validate_blueprint: hard issues. BlueprintEngine + Pydantic already guarantee
  structural completeness before a Blueprint reaches the Runtime, so the only
  thing left to catch here is an empty identity.slug — a Blueprint with no slug
  can't be cached, logged, or referenced safely. Runtime falls back to "default".
- blueprint_warnings: soft issues — a voice_intention or tone_ambience_key that
  doesn't resolve to anything. The downstream services already fall back
  gracefully in these cases, so the Blueprint is kept as-is; the warning exists
  purely so a blueprint author notices the typo.
"""

from __future__ import annotations

from app.services.llm.chat_provider import TONE_AMBIENCE
from app.services.llm.voice_mapping import INTENTION_VOICE_MAP

from .schema import Blueprint


def validate_blueprint(blueprint: Blueprint) -> list[str]:
    issues: list[str] = []
    if not blueprint.identity.slug:
        issues.append("identity.slug is empty")
    return issues


def blueprint_warnings(blueprint: Blueprint) -> list[str]:
    warnings: list[str] = []

    vc = blueprint.voice_configuration
    if vc.voice_intention.lower() not in INTENTION_VOICE_MAP:
        warnings.append(f"voice_intention '{vc.voice_intention}' has no voice mapping")

    key = blueprint.background_music_strategy.tone_ambience_key
    if key and key not in TONE_AMBIENCE:
        warnings.append(f"tone_ambience_key '{key}' has no ambience mapping")

    return warnings
