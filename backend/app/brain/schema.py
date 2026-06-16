"""
Memory architecture types for Echo Brain.

Conceptually separates memory into three scopes for future Blueprints:
- universal: identity, goals, relationships, preferences — spans all experiences
- experience: knowledge specific to one Blueprint (e.g. preferred grounding exercises
  for Peace) — not yet populated; storage/extraction for this scope ships in a later sprint
- session: the active conversation's transient context — not yet populated here,
  the conversation history itself already serves this role today

All three currently live in the same BrainMemory table; this is a logical
abstraction only, not a storage change.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MemoryBundle:
    universal: str
    experience: str = ""
    session: str = ""
