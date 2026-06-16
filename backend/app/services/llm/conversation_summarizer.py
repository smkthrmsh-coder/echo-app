"""
Rolling per-conversation summary — covers what falls outside the last-10-message
verbatim window sent to the LLM on every turn (see chat_provider.py). Mirrors
app/brain/extractor.py's Haiku-call pattern, but produces prose, not JSON facts.
"""

import logging

import anthropic
from sqlalchemy.orm import Session

from app.db.models import Conversation

logger = logging.getLogger(__name__)

_SYSTEM = """You maintain a rolling summary of an ongoing conversation between a user and Echo, \
an AI emotional companion.

You will be given the current summary (which may be empty, for a brand new conversation) and \
the next batch of messages. Update the summary to incorporate the new messages.

Keep it concise (under 200 words), in plain prose, capturing:
- What's been discussed so far
- The user's emotional throughline
- Any open topics, goals, or commitments worth remembering

Do not include meta-commentary like "the user said" repeatedly, headers, or bullet points.
Return ONLY the updated summary text, nothing else."""


async def summarize_conversation(previous_summary: str, new_messages: list[dict], api_key: str) -> str:
    if not new_messages or not api_key:
        return previous_summary

    conv_text = "\n".join(
        f"{m['role'].upper()}: {m['content'][:600]}" for m in new_messages if m.get("content")
    )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        temperature=0.3,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Current summary:\n{previous_summary or '(none yet)'}\n\n"
                f"New messages:\n{conv_text[:4000]}"
            ),
        }],
    )
    return response.content[0].text.strip()


def get_conversation_summary_block(db: Session, conversation_id: str | None) -> str:
    if not conversation_id:
        return ""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv or not conv.summary:
        return ""
    return f"[CONVERSATION SO FAR]\n{conv.summary}\n[/CONVERSATION SO FAR]"
