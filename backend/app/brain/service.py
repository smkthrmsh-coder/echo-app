"""
EchoBrainService — public API for the foundational memory engine.

Responsibilities:
- extract_from_conversation: runs after each conversation (background task)
- get_context_for_user: fast DB query returns formatted context for LLM injection
- update_temporal_statuses: transitions upcoming→active→completed based on dates
"""

from __future__ import annotations

import json
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import BrainMemory

from .extractor import extract_memories
from .schema import MemoryBundle

logger = logging.getLogger(__name__)

_IMPORTANCE_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class EchoBrainService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Extraction (runs as background task after each conversation) ───────────

    async def extract_from_conversation(self, user_id: str, messages: list[dict]) -> None:
        settings = get_settings()
        raw = await extract_memories(messages, settings.anthropic_api_key)
        saved = 0

        for m in raw:
            title = (m.get("title") or "")[:255].strip()
            category = m.get("category", "general")
            if not title:
                continue

            existing = (
                self.db.query(BrainMemory)
                .filter(
                    BrainMemory.user_id == user_id,
                    BrainMemory.title == title,
                    BrainMemory.category == category,
                )
                .first()
            )

            if existing:
                existing.description = m.get("description", existing.description)
                existing.confidence = float(m.get("confidence", existing.confidence))
                existing.importance = m.get("importance", existing.importance)
                existing.valid_from = m.get("valid_from")
                existing.valid_until = m.get("valid_until")
                existing.status = m.get("status", existing.status)
                existing.tags = json.dumps(m.get("tags", []))
            else:
                self.db.add(BrainMemory(
                    user_id=user_id,
                    category=category,
                    lifecycle=m.get("lifecycle", "semi_permanent"),
                    title=title,
                    description=(m.get("description") or "")[:2000],
                    confidence=float(m.get("confidence", 0.7)),
                    importance=m.get("importance", "medium"),
                    tags=json.dumps(m.get("tags", [])),
                    valid_from=m.get("valid_from"),
                    valid_until=m.get("valid_until"),
                    status=m.get("status", "active"),
                ))
                saved += 1

        try:
            self.db.commit()
            updated = len(raw) - saved
            uid = user_id[:8]
            logger.info(f"Echo Brain: {saved} new + {updated} updated memories for user {uid}")
        except Exception as exc:
            self.db.rollback()
            logger.warning(f"Brain memory save failed: {exc}")

    # ── Temporal transitions ───────────────────────────────────────────────────

    def update_temporal_statuses(self, user_id: str) -> None:
        today = date.today().isoformat()
        try:
            self.db.query(BrainMemory).filter(
                BrainMemory.user_id == user_id,
                BrainMemory.status == "upcoming",
                BrainMemory.valid_from <= today,
            ).update({"status": "active"}, synchronize_session=False)

            self.db.query(BrainMemory).filter(
                BrainMemory.user_id == user_id,
                BrainMemory.status == "active",
                BrainMemory.valid_until.isnot(None),
                BrainMemory.valid_until < today,
            ).update({"status": "completed"}, synchronize_session=False)

            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.warning(f"Brain temporal update failed: {exc}")

    # ── Context retrieval (synchronous — just a DB read) ──────────────────────

    def get_context_for_user(self, user_id: str) -> str:
        self.update_temporal_statuses(user_id)

        memories = (
            self.db.query(BrainMemory)
            .filter(BrainMemory.user_id == user_id, BrainMemory.status == "active")
            .all()
        )
        if not memories:
            return ""

        memories.sort(key=lambda m: (_IMPORTANCE_ORDER.get(m.importance, 4), -m.confidence))
        memories = memories[:10]

        goals = [m for m in memories if m.category == "goal"]
        events = [m for m in memories if m.category == "event"]
        rest = [m for m in memories if m.category not in ("goal", "event")]

        lines = ["[ECHO BRAIN — What you know about this person]"]

        for m in rest[:5]:
            lines.append(f"• {m.title}: {m.description}")

        if goals:
            lines.append("\nTheir goals:")
            for m in goals[:3]:
                lines.append(f"• {m.title}: {m.description}")

        if events:
            lines.append("\nUpcoming/recent events:")
            for m in events[:3]:
                lines.append(f"• {m.title}: {m.description}")

        lines.append("[/ECHO BRAIN]")
        return "\n".join(lines)

    # ── Single public retrieval API for Experience OS / future Blueprints ──────

    def retrieve_context(self, user_id: str) -> MemoryBundle:
        """
        The one retrieval entry point Blueprints should use — they should never
        query BrainMemory directly. Today only universal memory exists; experience
        and session scopes are placeholders for future sprints.
        """
        return MemoryBundle(universal=self.get_context_for_user(user_id))
