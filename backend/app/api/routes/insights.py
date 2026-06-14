"""
Insights route — aggregated user data.
Locked until 5 conversations; unlocks progressively.
"""

from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Conversation, Message, Memory, DailyStreak
from app.api.routes.journeys import _calc_streak
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

UNLOCK_THRESHOLD = 3  # conversations needed to unlock insights


class InsightsOut(BaseModel):
    locked: bool
    conversations_until_unlock: int
    total_conversations: int
    total_messages: int
    total_memories: int
    current_streak: int
    top_tones: list[dict]        # [{"tone": "calm", "count": 12, "emoji": "🌊"}]
    top_voices: list[dict]       # [{"name": "Sofia", "count": 8}]
    emotion_breakdown: list[dict] # [{"emotion": "anxious", "count": 5, "pct": 33}]
    most_active_style: str
    average_session_length: float  # minutes
    total_audio_minutes: float


TONE_EMOJI = {
    "energetic": "⚡", "calm": "🌊", "fierce": "🔥", "comforting": "🤗",
    "melancholic": "🌧", "playful": "✨", "mysterious": "🌙",
    "romantic": "🌹", "anxious": "💨", "hopeful": "🌅",
}


@router.get("/insights", response_model=InsightsOut, tags=["insights"])
def get_insights(db: Session = Depends(get_db)) -> InsightsOut:
    total_conversations = db.query(Conversation).count()
    conversations_until_unlock = max(0, UNLOCK_THRESHOLD - total_conversations)
    locked = total_conversations < UNLOCK_THRESHOLD

    if locked:
        return InsightsOut(
            locked=True,
            conversations_until_unlock=conversations_until_unlock,
            total_conversations=total_conversations,
            total_messages=0,
            total_memories=0,
            current_streak=0,
            top_tones=[],
            top_voices=[],
            emotion_breakdown=[],
            most_active_style="",
            average_session_length=0.0,
            total_audio_minutes=0.0,
        )

    all_messages = db.query(Message).all()
    asst_messages = [m for m in all_messages if m.role == "assistant"]

    total_messages = len(all_messages)
    total_memories = db.query(Memory).count()
    current_streak = _calc_streak(db)

    # Top tones
    tone_counts = Counter(m.tone for m in asst_messages if m.tone)
    top_tones = [
        {"tone": tone, "count": count, "emoji": TONE_EMOJI.get(tone, "✦")}
        for tone, count in tone_counts.most_common(5)
    ]

    # Top voices (personas)
    voice_counts = Counter(m.voice_name for m in asst_messages if m.voice_name)
    top_voices = [
        {"name": name, "count": count}
        for name, count in voice_counts.most_common(3)
    ]

    # Emotion breakdown from conversation.emotion field
    convs = db.query(Conversation).all()
    emotion_counts = Counter(c.emotion for c in convs if c.emotion)
    total_with_emotion = sum(emotion_counts.values()) or 1
    emotion_breakdown = [
        {"emotion": e, "count": c, "pct": round(c / total_with_emotion * 100)}
        for e, c in emotion_counts.most_common(5)
    ]

    # Most active speaking style
    style_counter: Counter = Counter()
    for c in convs:
        import json
        try:
            styles = json.loads(c.speaking_styles or "[]")
            style_counter.update(styles)
        except Exception:
            pass
    most_active_style = style_counter.most_common(1)[0][0] if style_counter else "balanced"

    # Audio stats
    durations = [m.duration_seconds for m in asst_messages if m.duration_seconds]
    total_audio_seconds = sum(durations)
    avg_session = (total_audio_seconds / max(len(durations), 1)) / 60
    total_audio_minutes = total_audio_seconds / 60

    return InsightsOut(
        locked=False,
        conversations_until_unlock=0,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_memories=total_memories,
        current_streak=current_streak,
        top_tones=top_tones,
        top_voices=top_voices,
        emotion_breakdown=emotion_breakdown,
        most_active_style=most_active_style,
        average_session_length=round(avg_session, 1),
        total_audio_minutes=round(total_audio_minutes, 1),
    )
