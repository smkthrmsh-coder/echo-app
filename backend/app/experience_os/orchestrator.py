"""
ExperienceOS — the central coordinator for every user interaction.

It orchestrates blueprint loading and Echo Brain retrieval; it does not own any
business logic itself (the actual LLM/TTS pipeline calls, voice resolution, and
prompt text all remain exactly where they were). This sprint wires it into the
two places conversations.py used to call EchoBrainService directly — the
returned brain_context is byte-identical to what get_context_for_user()
returned before.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.brain.service import EchoBrainService
from app.services.llm.conversation_summarizer import get_conversation_summary_block

from .blueprint_engine import get_engine
from .context import ExperienceContext


class ExperienceOS:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.brain = EchoBrainService(db)
        self.blueprint_engine = get_engine()

    def prepare_experience(
        self, user_id: str, intention: str | None, conversation_id: str | None = None
    ) -> ExperienceContext:
        blueprint = self.blueprint_engine.load(intention)
        bundle = self.brain.retrieve_context(user_id)
        summary_block = get_conversation_summary_block(self.db, conversation_id)
        combined_context = "\n\n".join(p for p in [bundle.universal, summary_block] if p)
        return ExperienceContext(
            user_id=user_id,
            intention=intention,
            blueprint=blueprint,
            brain_context=combined_context,
        )
