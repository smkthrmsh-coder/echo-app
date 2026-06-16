"""
LLM-based memory extraction from conversations.
Uses claude-haiku for speed and cost efficiency.
"""

import json
import logging
from datetime import date

import anthropic

logger = logging.getLogger(__name__)

_SYSTEM = """You are Echo Brain, an AI memory extraction system for an emotional support companion.

Analyze this conversation and extract structured, lasting memories about the USER (not Echo's responses).

EXTRACT information with clear lasting value:
- Specific goals with context ("preparing for job interview at Google next month")
- Life events with timing ("got promoted last week", "moving to Singapore in July")
- Named relationships ("manager Sarah gives unclear feedback", "best friend Priya just got engaged")
- Concrete preferences ("responds better to direct advice than validation", "hates platitudes")
- Achievements ("ran first half-marathon", "launched first product")
- Recurring challenges ("struggles to switch off from work at night", "anxiety before presentations")
- Identity/career context ("founder of early-stage startup", "just started therapy")

DO NOT extract:
- Temporary emotional states ("feeling stressed today", "tired right now")
- Vague statements without specific details ("I work hard", "life is busy")
- What Echo said, suggested, or asked
- Uncertain inferences or assumptions

Return ONLY a JSON array. Empty [] if nothing worth storing.
[{
  "category": "goal|event|relationship|preference|achievement|challenge|identity",
  "lifecycle": "permanent|semi_permanent|temporary",
  "title": "Short memorable title (max 60 chars)",
  "description": "Specific detail using user's own words (1-2 sentences max)",
  "confidence": 0.75,
  "importance": "critical|high|medium|low",
  "tags": ["tag1"],
  "valid_from": "YYYY-MM-DD or null",
  "valid_until": "YYYY-MM-DD or null",
  "status": "active|upcoming|completed"
}]

lifecycle: permanent=core identity/long-term, semi_permanent=months horizon, temporary=specific dated event
importance: critical=changes how Echo responds every time, high=important context, medium=useful, low=minor"""


async def extract_memories(messages: list[dict], api_key: str) -> list[dict]:
    if not messages or not api_key:
        return []

    # Only include substantive messages (skip very short ones)
    filtered = [m for m in messages if m.get("content") and len(m["content"]) > 10]
    if not filtered:
        return []

    conv_text = "\n".join(
        f"{m['role'].upper()}: {m['content'][:600]}" for m in filtered
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            temperature=0.2,
            system=_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Today's date: {date.today().isoformat()}\n\nConversation to analyze:\n{conv_text[:4000]}",
            }],
        )
        raw = response.content[0].text.strip()
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        return json.loads(raw[start:end])
    except Exception as exc:
        logger.warning(f"Memory extraction failed: {exc}")
        return []
