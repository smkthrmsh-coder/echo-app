"""
BlueprintEngine — loads, validates, and caches Blueprint definitions.

Voice IDs are never duplicated into YAML. Each Blueprint's voice_configuration
stores only a `voice_intention` key; this engine resolves the real ElevenLabs
IDs from app.services.llm.voice_mapping (the existing single source of truth)
at load time.

The cache is in-memory and never invalidated — changing a YAML file requires a
process restart. Acceptable for this sprint's placeholder blueprints; see
docs/ARCHITECTURE.md.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.core.logging import get_logger
from app.services.llm.voice_mapping import INTENTION_VOICE_MAP

from .schema import Blueprint

logger = get_logger(__name__)

_BLUEPRINTS_DIR = Path(__file__).parent / "blueprints"
_DEFAULT_SLUG = "default"


class BlueprintEngine:
    def __init__(self) -> None:
        self._cache: dict[str, Blueprint] = {}

    def load(self, slug: str | None) -> Blueprint:
        key = (slug or _DEFAULT_SLUG).lower()
        if key in self._cache:
            return self._cache[key]

        blueprint = self._load_from_disk(key)
        if blueprint is None:
            if key != _DEFAULT_SLUG:
                logger.warning(f"Blueprint '{key}' invalid or missing — falling back to default")
                blueprint = self._cache.get(_DEFAULT_SLUG) or self._load_from_disk(_DEFAULT_SLUG)
            if blueprint is None:
                # Last-resort in-memory fallback so the engine never raises into callers.
                blueprint = Blueprint(identity={"slug": _DEFAULT_SLUG, "display_name": "Default"})

        blueprint = self._resolve_voice(blueprint)
        self._cache[key] = blueprint
        return blueprint

    def _load_from_disk(self, slug: str) -> Blueprint | None:
        path = _BLUEPRINTS_DIR / f"{slug}.yaml"
        if not path.exists():
            return None
        try:
            raw = yaml.safe_load(path.read_text()) or {}
            return Blueprint(**raw)
        except yaml.YAMLError as exc:
            logger.warning(f"Blueprint '{slug}' has invalid YAML: {exc}")
            return None
        except ValidationError as exc:
            logger.warning(f"Blueprint '{slug}' failed schema validation: {exc}")
            return None

    def _resolve_voice(self, blueprint: Blueprint) -> Blueprint:
        vc = blueprint.voice_configuration
        iv = INTENTION_VOICE_MAP.get(vc.voice_intention.lower())
        if iv is None:
            return blueprint
        vc.resolved_male_voice_id = iv.male_id
        vc.resolved_female_voice_id = iv.female_id
        vc.resolved_stability = iv.stability
        vc.resolved_similarity_boost = iv.similarity_boost
        vc.resolved_style = iv.style
        return blueprint


_engine = BlueprintEngine()


def get_engine() -> BlueprintEngine:
    """Shared singleton so every caller (ExperienceOS, BlueprintRuntime, ...) hits one cache."""
    return _engine
