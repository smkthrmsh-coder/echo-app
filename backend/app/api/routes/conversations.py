import json
import re
from datetime import date
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.brain.service import EchoBrainService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import Conversation, DailyStreak, Message, User
from app.experience_os.orchestrator import ExperienceOS
from app.experience_os.runtime import BlueprintRuntime
from app.models.requests import (
    ConversationOut,
    ConversationSummaryOut,
    CreateConversationRequest,
    MessageOut,
    SendMessageRequest,
    UpdateConversationRequest,  # noqa: F401
)
from app.services.emotion.chat_pipeline import run_chat_pipeline
from app.services.emotion.pipeline import run_pipeline
from app.services.llm.conversation_summarizer import summarize_conversation

router = APIRouter()
logger = get_logger(__name__)

BLUEPRINT_ENABLED_INTENTIONS = {
    "peace", "motivation", "confidence", "comfort", "sleep",
    "focus", "clarity", "energy", "encouragement",
}
SUMMARY_UPDATE_INTERVAL = 8


def _clean_for_display(text: str) -> str:
    text = re.sub(r"<break\s+[^>]*/?>", "", text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()


def _msg_to_out(msg: Message) -> MessageOut:
    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        content=msg.content,
        audio_url=f"/api/chat-audio/{msg.id}" if msg.audio_path else None,
        duration_seconds=msg.duration_seconds,
        voice_name=msg.voice_name,
        tone=msg.tone,
        created_at=msg.created_at.isoformat(),
    )


def _conv_to_out(conv: Conversation, messages: list[Message]) -> ConversationOut:
    styles = json.loads(conv.speaking_styles) if conv.speaking_styles else []
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        speaking_styles=styles,
        gender=conv.gender,
        energy_level=conv.energy_level,
        persona_id=conv.persona_id,
        emotion=conv.emotion,
        is_pinned=conv.is_pinned,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        messages=[_msg_to_out(m) for m in messages],
    )


def _record_streak(db: Session) -> None:
    today = date.today().isoformat()
    row = db.query(DailyStreak).filter(DailyStreak.date_str == today).first()
    if row:
        row.conversation_count += 1
    else:
        db.add(DailyStreak(date_str=today))


@router.post("/conversations", response_model=ConversationOut, tags=["chat"])
async def create_conversation(
    request: CreateConversationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationOut:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    intention = request.emotion or None

    try:
        if intention in BLUEPRINT_ENABLED_INTENTIONS:
            runtime = BlueprintRuntime(db)
            experience = await runtime.execute(
                current_user.id,
                request.initial_prompt,
                intention=intention,
                celebrity_voice_id=request.celebrity_voice_id,
                gender=request.gender or None,
                speaking_styles=request.speaking_styles or None,
                username=current_user.display_name or request.username or "there",
            )
            profile, audio_path, duration = (
                experience.profile, experience.audio_path, experience.duration_seconds
            )
        else:
            # Experience OS prepares the experience context (blueprint + brain memory) for this turn
            experience_os = ExperienceOS(db)
            exp_ctx = experience_os.prepare_experience(current_user.id, intention)
            brain_context = exp_ctx.brain_context

            profile, audio_path, duration = await run_pipeline(
                request.initial_prompt,
                celebrity_voice_id=request.celebrity_voice_id,
                gender=request.gender or None,
                speaking_styles=request.speaking_styles or None,
                username=current_user.display_name or request.username or "there",
                intention=intention,
                brain_context=brain_context or None,
            )
    except Exception as exc:
        logger.exception("Pipeline failed for new conversation")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    title = request.title or profile.experience_title or "New Conversation"
    styles_json = json.dumps(request.speaking_styles)

    conv = Conversation(
        user_id=current_user.id,
        title=title,
        speaking_styles=styles_json,
        gender=request.gender,
        energy_level=request.energy_level,
        persona_id=request.persona_id,
        emotion=request.emotion,
        voice_id=profile.voice_id,
        voice_name=profile.voice_name,
    )
    db.add(conv)
    db.flush()

    db.add(Message(conversation_id=conv.id, role="user", content=request.initial_prompt, voice_name="", tone=""))
    db.add(Message(
        conversation_id=conv.id, role="assistant",
        content=_clean_for_display(profile.script), audio_path=audio_path,
        duration_seconds=duration, voice_name=profile.voice_name, tone=profile.tone.value,
    ))

    _record_streak(db)
    db.commit()

    messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    msgs_for_brain = [{"role": m.role, "content": m.content} for m in messages]

    # Extract memories in background — doesn't block response
    background_tasks.add_task(_run_brain_extraction, current_user.id, msgs_for_brain)

    return _conv_to_out(conv, messages)


async def _run_brain_extraction(user_id: str, messages: list[dict]) -> None:
    """Background task: extract memories from conversation messages."""
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        brain = EchoBrainService(db)
        await brain.extract_from_conversation(user_id, messages)
    except Exception as exc:
        logger.warning(f"Background brain extraction failed: {exc}")
    finally:
        db.close()


async def _run_conversation_summary_update(conversation_id: str) -> None:
    """Background task: roll the conversation's summary forward to cover new messages."""
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )
        new_segment = [
            {"role": m.role, "content": m.content} for m in messages[conv.summarized_through_count:]
        ]
        if not new_segment:
            return
        settings = get_settings()
        conv.summary = await summarize_conversation(conv.summary, new_segment, settings.anthropic_api_key)
        conv.summarized_through_count = len(messages)
        db.commit()
    except Exception as exc:
        logger.warning(f"Background conversation summary update failed: {exc}")
    finally:
        db.close()


@router.get("/conversations", response_model=list[ConversationSummaryOut], tags=["chat"])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationSummaryOut]:
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        .all()
    )
    result = []
    for conv in convs:
        msgs = db.query(Message).filter(Message.conversation_id == conv.id).all()
        preview = next((m.content[:80] for m in reversed(msgs) if m.role == "assistant"), "")
        result.append(ConversationSummaryOut(
            id=conv.id, title=conv.title, preview=preview,
            message_count=len(msgs), is_pinned=conv.is_pinned,
            emotion=conv.emotion,
            created_at=conv.created_at.isoformat(), updated_at=conv.updated_at.isoformat(),
        ))
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationOut, tags=["chat"])
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationOut:
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    return _conv_to_out(conv, msgs)


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut, tags=["chat"])
def update_conversation(
    conversation_id: str,
    request: "UpdateConversationRequest",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationOut:
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if request.title is not None:
        conv.title = request.title
    if request.is_pinned is not None:
        conv.is_pinned = request.is_pinned
    if request.reset_voice:
        conv.voice_id = ""
        conv.voice_name = ""
    if request.gender is not None:
        conv.gender = request.gender
    db.commit()
    msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    return _conv_to_out(conv, msgs)


@router.delete("/conversations/{conversation_id}", tags=["chat"])
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = db.query(Message).filter(Message.conversation_id == conversation_id).all()
    for msg in msgs:
        if msg.audio_path:
            Path(msg.audio_path).unlink(missing_ok=True)
        db.delete(msg)
    db.delete(conv)
    db.commit()
    return {"deleted": True}


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, tags=["chat"])
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageOut:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    intention = conv.emotion or None

    user_msg = Message(conversation_id=conv.id, role="user", content=request.content, voice_name="", tone="")
    db.add(user_msg)
    db.flush()

    prev_msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    history = [{"role": m.role, "content": m.content} for m in prev_msgs if m.id != user_msg.id]
    styles = json.loads(conv.speaking_styles) if conv.speaking_styles else []

    try:
        if intention in BLUEPRINT_ENABLED_INTENTIONS:
            runtime = BlueprintRuntime(db)
            experience = await runtime.execute_reply(
                current_user.id,
                user_message=request.content,
                history=history,
                speaking_styles=styles,
                gender=conv.gender,
                energy_level=conv.energy_level,
                intention=intention,
                emotional_mode=request.emotional_mode,
                celebrity_voice_id=request.celebrity_voice_id,
                locked_voice_id=conv.voice_id or None,
                locked_voice_name=conv.voice_name or None,
                conversation_id=conv.id,
            )
            profile, audio_path, duration = (
                experience.profile, experience.audio_path, experience.duration_seconds
            )
        else:
            # Experience OS prepares the experience context (blueprint + brain memory) for this turn
            experience_os = ExperienceOS(db)
            exp_ctx = experience_os.prepare_experience(current_user.id, intention, conversation_id=conv.id)
            brain_context = exp_ctx.brain_context

            profile, audio_path, duration = await run_chat_pipeline(
                user_message=request.content,
                history=history,
                speaking_styles=styles,
                gender=conv.gender,
                energy_level=conv.energy_level,
                emotional_mode=request.emotional_mode,
                celebrity_voice_id=request.celebrity_voice_id,
                locked_voice_id=conv.voice_id or None,
                locked_voice_name=conv.voice_name or None,
                intention=intention,
                brain_context=brain_context or None,
            )
    except Exception as exc:
        logger.exception("Chat pipeline failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    asst_msg = Message(
        conversation_id=conv.id, role="assistant",
        content=_clean_for_display(profile.script), audio_path=audio_path,
        duration_seconds=duration, voice_name=profile.voice_name, tone=profile.tone.value,
    )
    db.add(asst_msg)

    from datetime import datetime
    conv.updated_at = datetime.utcnow()
    _record_streak(db)
    db.commit()

    # Extract memories in background after reply
    all_msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    msgs_for_brain = [{"role": m.role, "content": m.content} for m in all_msgs[-6:]]  # last 6 messages
    background_tasks.add_task(_run_brain_extraction, current_user.id, msgs_for_brain)

    if len(all_msgs) - conv.summarized_through_count >= SUMMARY_UPDATE_INTERVAL:
        background_tasks.add_task(_run_conversation_summary_update, conv.id)

    return _msg_to_out(asst_msg)


@router.get("/chat-audio/{message_id}", tags=["chat"])
def get_chat_audio(message_id: str, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg or not msg.audio_path:
        raise HTTPException(status_code=404, detail="Audio not found")
    if not Path(msg.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    return FileResponse(path=msg.audio_path, media_type="audio/mpeg", filename=f"{message_id}.mp3")
