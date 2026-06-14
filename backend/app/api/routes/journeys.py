"""
Journey routes — guided multi-day programs.
Templates are hardcoded; user progress is stored in user_journeys table.
"""

import json
from datetime import datetime, date
from pathlib import Path

import anthropic as anthropic_sdk
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import UserJourney, DailyStreak
from app.core.logging import get_logger
from app.models.emotion import EmotionProfile, EmotionalTone, NarrationStyle, Pacing, VoiceSettings
from app.services.tts.factory import get_tts_provider

router = APIRouter()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Journey templates — the catalog
# ---------------------------------------------------------------------------

JOURNEY_TEMPLATES = [
    {
        "slug": "better-sleep",
        "title": "Better Sleep",
        "emoji": "🌙",
        "tagline": "Wind down. Rest deeper. Wake better.",
        "description": "A gentle 7-day program to build a calming bedtime ritual and improve sleep quality.",
        "duration_days": 7,
        "category": "wellness",
        "color": "#6366F1",
        "daily_prompts": [
            "I want to wind down before bed and calm my racing thoughts.",
            "Help me release the stress of today so I can sleep peacefully.",
            "I need a gentle bedtime ritual to ease into rest.",
            "Guide me through relaxing my body completely before sleep.",
            "Help me let go of tomorrow's worries and be present tonight.",
            "I want to feel deeply at peace as I prepare for sleep.",
            "Tonight I want to celebrate one week of better sleep habits.",
        ],
    },
    {
        "slug": "interview-confidence",
        "title": "Interview Confidence",
        "emoji": "💼",
        "tagline": "Walk in ready. Walk out proud.",
        "description": "7 days of mindset coaching to help you prepare, perform, and own the room.",
        "duration_days": 7,
        "category": "career",
        "color": "#F59E0B",
        "daily_prompts": [
            "I have an interview coming up and I need to build confidence.",
            "Help me work through my anxiety about being judged in interviews.",
            "I want to practice telling my story clearly and powerfully.",
            "Help me get into the mindset of a top performer before my interview.",
            "I need to reframe rejection and build resilience for the process.",
            "Help me visualize success and anchor my confidence.",
            "I'm going into my interview today. Help me feel ready and calm.",
        ],
    },
    {
        "slug": "anxiety-relief",
        "title": "Anxiety Relief",
        "emoji": "🌊",
        "tagline": "Less panic. More peace.",
        "description": "A 14-day companion for navigating anxiety with breathing, perspective, and calm.",
        "duration_days": 14,
        "category": "mental-health",
        "color": "#10B981",
        "daily_prompts": [
            "I've been feeling anxious and I need to calm down right now.",
            "Help me understand why I'm feeling this way and find some peace.",
            "I want to learn how to breathe through anxious moments.",
            "Help me identify what's really worrying me underneath the surface.",
            "I need to stop catastrophizing and find a grounded perspective.",
            "Help me build a toolkit for when anxiety spikes suddenly.",
            "I want to reflect on how I've handled stress this week.",
            "Help me find what calming practices actually work for me.",
            "I'm dealing with social anxiety today. Help me prepare.",
            "Help me create a morning routine that prevents anxiety from building.",
            "I need to address the physical symptoms of my anxiety.",
            "Help me reconnect with a sense of safety and calm today.",
            "I want to notice how far I've come in managing my anxiety.",
            "Help me close this journey with a toolkit for the future.",
        ],
    },
    {
        "slug": "breakup-recovery",
        "title": "Breakup Recovery",
        "emoji": "🌱",
        "tagline": "Heal at your own pace.",
        "description": "A 14-day journey through grief, healing, and rediscovering yourself.",
        "duration_days": 14,
        "category": "relationships",
        "color": "#EC4899",
        "daily_prompts": [
            "I just went through a breakup and I'm feeling devastated.",
            "I need to process feelings of anger and betrayal today.",
            "Help me understand what I want to learn from this relationship.",
            "I'm missing them today even though I know it's over.",
            "Help me reconnect with who I am outside of this relationship.",
            "I need to stop looking at their social media. Help me.",
            "Help me find things that genuinely make me happy right now.",
            "I want to reflect on what I deserve in a relationship.",
            "Help me deal with seeing them happy while I'm still hurting.",
            "I need to focus on building my own life and identity.",
            "Help me write a letter I'll never send, to get closure.",
            "I want to celebrate small wins in my healing process.",
            "Help me envision who I want to become from this experience.",
            "I'm closing this chapter. Help me say goodbye with grace.",
        ],
    },
    {
        "slug": "deep-focus",
        "title": "Deep Focus",
        "emoji": "🎯",
        "tagline": "Enter flow. Do your best work.",
        "description": "7 days of focus rituals, procrastination busting, and peak performance mindset.",
        "duration_days": 7,
        "category": "productivity",
        "color": "#8B5CF6",
        "daily_prompts": [
            "I need to get into deep focus but I keep getting distracted.",
            "Help me overcome procrastination on a project I've been avoiding.",
            "I want to build a morning routine that sets me up for focused work.",
            "Help me design my ideal environment for concentration.",
            "I need to manage my energy, not just my time. Help me think through this.",
            "Help me stay focused when everything feels urgent and overwhelming.",
            "I want to reflect on what made me most productive this week.",
        ],
    },
    {
        "slug": "self-confidence",
        "title": "Self Confidence",
        "emoji": "⚡",
        "tagline": "Own who you are.",
        "description": "A 21-day journey to build genuine self-belief from the inside out.",
        "duration_days": 21,
        "category": "personal-growth",
        "color": "#F97316",
        "daily_prompts": [
            "I struggle with self-confidence and I want to change that.",
            "Help me identify where my self-doubt comes from.",
            "I want to practice speaking to myself with more kindness.",
            "Help me recognize my genuine strengths without feeling arrogant.",
            "I keep comparing myself to others. Help me stop.",
            "Help me take one action today that scares me a little.",
            "I want to reflect on a past win that I've been dismissing.",
            "Help me define what confidence actually means for me personally.",
            "I need to handle criticism better without collapsing inside.",
            "Help me build presence — how I carry myself, my voice, my space.",
            "I want to address the inner critic that narrates my life.",
            "Help me celebrate one thing I've done well this week.",
            "I need to set a boundary today. Help me prepare.",
            "Help me reconnect with what makes me genuinely proud of myself.",
            "I want to work on being more confident in social situations.",
            "Help me own my opinions without needing everyone to agree.",
            "I need to stop apologizing for taking up space.",
            "Help me build a morning affirmation practice that feels real.",
            "I want to reflect on who I was at the start of this journey.",
            "Help me articulate the person I'm becoming.",
            "I'm closing this journey. Help me commit to my new self.",
        ],
    },
]

JOURNEY_MAP = {j["slug"]: j for j in JOURNEY_TEMPLATES}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class JourneyTemplate(BaseModel):
    slug: str
    title: str
    emoji: str
    tagline: str
    description: str
    duration_days: int
    category: str
    color: str


class UserJourneyOut(BaseModel):
    id: str
    journey_slug: str
    journey: JourneyTemplate
    current_day: int
    completed_days: list[int]
    is_active: bool
    started_at: str
    last_session_at: str | None
    today_prompt: str | None


class StreakOut(BaseModel):
    current_streak: int
    total_days: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today() -> str:
    return date.today().isoformat()


def _calc_streak(db: Session) -> int:
    rows = db.query(DailyStreak).order_by(DailyStreak.date_str.desc()).all()
    if not rows:
        return 0
    today = date.today()
    streak = 0
    for row in rows:
        d = date.fromisoformat(row.date_str)
        expected = date.fromordinal(today.toordinal() - streak)
        if d == expected:
            streak += 1
        else:
            break
    return streak


def _uj_to_out(uj: UserJourney) -> UserJourneyOut:
    template = JOURNEY_MAP.get(uj.journey_slug, {})
    completed = json.loads(uj.completed_days or "[]")
    prompts = template.get("daily_prompts", [])
    today_prompt = prompts[uj.current_day - 1] if 0 < uj.current_day <= len(prompts) else None
    return UserJourneyOut(
        id=uj.id,
        journey_slug=uj.journey_slug,
        journey=JourneyTemplate(**{k: template[k] for k in JourneyTemplate.model_fields}),
        current_day=uj.current_day,
        completed_days=completed,
        is_active=uj.is_active,
        started_at=uj.started_at.isoformat(),
        last_session_at=uj.last_session_at.isoformat() if uj.last_session_at else None,
        today_prompt=today_prompt,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/journeys", response_model=list[JourneyTemplate], tags=["journeys"])
def list_journeys() -> list[JourneyTemplate]:
    return [JourneyTemplate(**{k: j[k] for k in JourneyTemplate.model_fields}) for j in JOURNEY_TEMPLATES]


@router.get("/journeys/active", response_model=UserJourneyOut | None, tags=["journeys"])
def get_active_journey(db: Session = Depends(get_db)) -> UserJourneyOut | None:
    uj = db.query(UserJourney).filter(UserJourney.is_active == True).order_by(UserJourney.started_at.desc()).first()  # noqa: E712
    if not uj:
        return None
    return _uj_to_out(uj)


@router.post("/journeys/{slug}/start", response_model=UserJourneyOut, tags=["journeys"])
def start_journey(slug: str, db: Session = Depends(get_db)) -> UserJourneyOut:
    if slug not in JOURNEY_MAP:
        raise HTTPException(status_code=404, detail=f"Journey '{slug}' not found")

    # Deactivate any existing active journey
    existing = db.query(UserJourney).filter(UserJourney.is_active == True).all()  # noqa: E712
    for uj in existing:
        uj.is_active = False

    uj = UserJourney(journey_slug=slug, current_day=1, completed_days="[]")
    db.add(uj)
    db.commit()
    db.refresh(uj)
    logger.info(f"Started journey: {slug}")
    return _uj_to_out(uj)


@router.post("/journeys/{slug}/checkin", response_model=UserJourneyOut, tags=["journeys"])
def checkin_journey(slug: str, db: Session = Depends(get_db)) -> UserJourneyOut:
    uj = db.query(UserJourney).filter(
        UserJourney.journey_slug == slug,
        UserJourney.is_active == True,  # noqa: E712
    ).first()
    if not uj:
        raise HTTPException(status_code=404, detail="No active journey with this slug")

    template = JOURNEY_MAP[slug]
    completed = json.loads(uj.completed_days or "[]")

    if uj.current_day not in completed:
        completed.append(uj.current_day)
        uj.completed_days = json.dumps(completed)

    if uj.current_day < template["duration_days"]:
        uj.current_day += 1
    else:
        uj.is_active = False  # journey complete

    uj.last_session_at = datetime.utcnow()

    # Log streak
    today = _today()
    row = db.query(DailyStreak).filter(DailyStreak.date_str == today).first()
    if row:
        row.conversation_count += 1
    else:
        db.add(DailyStreak(date_str=today))

    db.commit()
    db.refresh(uj)
    return _uj_to_out(uj)


@router.post("/journeys/{slug}/abandon", tags=["journeys"])
def abandon_journey(slug: str, db: Session = Depends(get_db)) -> dict:
    uj = db.query(UserJourney).filter(
        UserJourney.journey_slug == slug,
        UserJourney.is_active == True,  # noqa: E712
    ).first()
    if uj:
        uj.is_active = False
        db.commit()
    return {"abandoned": True}


_SESSION_CONFIGS: dict[str, dict] = {
    "wellness": {
        "system": (
            "You are a deeply calming sleep guide creating a 2-minute bedtime audio session.\n\n"
            "Write a spoken-word script of approximately 185-210 words.\n\n"
            "Pacing: Very slow. Use long, unhurried sentences. Let silence exist between thoughts — "
            "commas and full stops are breathing room. Never rush. This script should feel like a "
            "warm weighted blanket settling over the listener.\n\n"
            "Guidelines:\n"
            "- Speak directly to the listener: 'you', 'your'\n"
            "- Open by asking them to close their eyes and take a single, slow breath\n"
            "- Gently guide their attention through their body — softening, releasing\n"
            "- Close by letting them drift, with permission to simply rest\n"
            "- Continuous prose only. No headers, no stage directions."
        ),
        "voice_settings": VoiceSettings(stability=0.62, similarity_boost=0.72, style=0.22, use_speaker_boost=True),
        "tone": EmotionalTone.CALM,
    },
    "mental-health": {
        "system": (
            "You are a grounding, compassionate anxiety guide creating a 2-minute audio session.\n\n"
            "Write a spoken-word script of approximately 200-220 words.\n\n"
            "Pacing: Slow and steady. Anchor sentences in the present moment. Use short, clear sentences "
            "to create safety. The listener may feel scattered — bring them back gently.\n\n"
            "Guidelines:\n"
            "- Begin with a breath: simple, immediate, grounding\n"
            "- Name what they might be feeling without judgment\n"
            "- Guide them toward a sense of safety and control in their own body\n"
            "- End with a quiet affirmation they can carry with them\n"
            "- Continuous prose only."
        ),
        "voice_settings": VoiceSettings(stability=0.56, similarity_boost=0.72, style=0.35, use_speaker_boost=True),
        "tone": EmotionalTone.COMFORTING,
    },
    "relationships": {
        "system": (
            "You are a warm, compassionate guide helping someone heal from heartbreak, "
            "creating a 2-minute audio session.\n\n"
            "Write a spoken-word script of approximately 200-225 words.\n\n"
            "Pacing: Gentle and unhurried. Speak with real warmth — as a trusted friend who "
            "understands pain without dismissing it.\n\n"
            "Guidelines:\n"
            "- Acknowledge the weight of what they're carrying\n"
            "- Hold space — don't rush them toward 'feeling better'\n"
            "- Offer a small, grounded perspective they can hold onto today\n"
            "- Close with quiet encouragement and care\n"
            "- Continuous prose only."
        ),
        "voice_settings": VoiceSettings(stability=0.52, similarity_boost=0.72, style=0.42, use_speaker_boost=True),
        "tone": EmotionalTone.COMFORTING,
    },
    "career": {
        "system": (
            "You are a confident, encouraging coach creating a 2-minute pre-interview mindset session.\n\n"
            "Write a spoken-word script of approximately 210-235 words.\n\n"
            "Pacing: Clear and purposeful. Energising without being frantic. Each sentence should "
            "land with intention — this person is preparing to show up at their best.\n\n"
            "Guidelines:\n"
            "- Open by grounding them in their own capability\n"
            "- Remind them that preparation is already done — now it's about presence\n"
            "- Build quiet confidence, not hype\n"
            "- Close with a sharp, clear mantra they can take into the room\n"
            "- Continuous prose only."
        ),
        "voice_settings": VoiceSettings(stability=0.40, similarity_boost=0.72, style=0.60, use_speaker_boost=True),
        "tone": EmotionalTone.HOPEFUL,
    },
    "productivity": {
        "system": (
            "You are a sharp, focused coach creating a 2-minute deep-focus session.\n\n"
            "Write a spoken-word script of approximately 210-235 words.\n\n"
            "Pacing: Direct and crisp. No filler. Sentences that cut through mental fog and create "
            "a clear, quiet sense of purpose. The listener needs to get into flow state.\n\n"
            "Guidelines:\n"
            "- Open by clearing the mental clutter — let them name and then release distractions\n"
            "- Help them define one clear intention for the work ahead\n"
            "- Guide them into a focused, alert state of readiness\n"
            "- Close with an activation cue — a moment to begin\n"
            "- Continuous prose only."
        ),
        "voice_settings": VoiceSettings(stability=0.36, similarity_boost=0.72, style=0.65, use_speaker_boost=True),
        "tone": EmotionalTone.ENERGETIC,
    },
    "personal-growth": {
        "system": (
            "You are a warm, empowering coach creating a 2-minute self-confidence session.\n\n"
            "Write a spoken-word script of approximately 210-235 words.\n\n"
            "Pacing: Warm and building. Start steady, let conviction grow through the session. "
            "This isn't about hype — it's about helping someone genuinely feel their own worth.\n\n"
            "Guidelines:\n"
            "- Begin by acknowledging the courage it takes to show up for yourself\n"
            "- Challenge the inner critic gently but firmly\n"
            "- Build toward a specific, grounded sense of self-belief\n"
            "- Close with a powerful but honest affirmation\n"
            "- Continuous prose only."
        ),
        "voice_settings": VoiceSettings(stability=0.40, similarity_boost=0.72, style=0.58, use_speaker_boost=True),
        "tone": EmotionalTone.HOPEFUL,
    },
}

_DEFAULT_SESSION_CONFIG = _SESSION_CONFIGS["wellness"]


def _get_session_config(category: str) -> dict:
    return _SESSION_CONFIGS.get(category, _DEFAULT_SESSION_CONFIG)


async def _generate_session(slug: str, day: int, today_prompt: str, category: str) -> tuple[str, float]:
    """Generate audio for a journey session. Returns (audio_path, duration_seconds). Caches to disk."""
    settings = get_settings()
    audio_dir = Path(settings.audio_output_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)

    session_id = f"{slug}_day{day}"
    audio_path = audio_dir / f"journey_{session_id}.mp3"

    # Return cached file if it already exists
    if audio_path.exists():
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(str(audio_path), codec="mp3")
            return str(audio_path), len(seg) / 1000.0
        except Exception:
            audio_path.unlink(missing_ok=True)

    config = _get_session_config(category)

    # Generate script via Claude
    client = anthropic_sdk.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=config["system"],
        messages=[{"role": "user", "content": f"Session topic: {today_prompt}"}],
    )
    script = message.content[0].text.strip()

    # Convert to audio with category-tuned voice settings
    profile = EmotionProfile(
        tone=config["tone"],
        narration_style=NarrationStyle.GUIDE,
        pacing=Pacing.SLOW,
        voice_settings=config["voice_settings"],
        script=script,
    )
    tts = get_tts_provider()
    await tts.synthesize(profile, str(audio_path))

    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(str(audio_path), codec="mp3")
        duration = len(seg) / 1000.0
    except Exception:
        duration = 0.0

    return str(audio_path), duration


@router.post("/journeys/{slug}/session", tags=["journeys"])
async def generate_journey_session(slug: str, db: Session = Depends(get_db)) -> dict:
    if slug not in JOURNEY_MAP:
        raise HTTPException(status_code=404, detail=f"Journey '{slug}' not found")

    uj = db.query(UserJourney).filter(
        UserJourney.journey_slug == slug,
        UserJourney.is_active == True,  # noqa: E712
    ).first()
    if not uj:
        raise HTTPException(status_code=404, detail="No active journey with this slug")

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    template = JOURNEY_MAP[slug]
    prompts = template.get("daily_prompts", [])
    day = uj.current_day
    today_prompt = prompts[day - 1] if 0 < day <= len(prompts) else "A moment of stillness and presence."
    category = template.get("category", "wellness")

    try:
        audio_path, duration = await _generate_session(slug, day, today_prompt, category)
    except Exception as exc:
        logger.exception("Journey session generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session_id = f"{slug}_day{day}"
    return {
        "audio_url": f"/api/journey-audio/{session_id}",
        "duration_seconds": duration,
        "day": day,
        "today_prompt": today_prompt,
    }


@router.get("/journey-audio/{session_id}", tags=["journeys"])
def get_journey_audio(session_id: str) -> FileResponse:
    settings = get_settings()
    audio_dir = Path(settings.audio_output_dir)
    audio_path = audio_dir / f"journey_{session_id}.mp3"
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path=str(audio_path), media_type="audio/mpeg", filename=f"{session_id}.mp3")


@router.get("/streaks", response_model=StreakOut, tags=["journeys"])
def get_streak(db: Session = Depends(get_db)) -> StreakOut:
    total = db.query(DailyStreak).count()
    current = _calc_streak(db)
    return StreakOut(current_streak=current, total_days=total)


@router.post("/streaks/checkin", tags=["journeys"])
def daily_checkin(db: Session = Depends(get_db)) -> dict:
    today = _today()
    row = db.query(DailyStreak).filter(DailyStreak.date_str == today).first()
    if not row:
        db.add(DailyStreak(date_str=today))
        db.commit()
        return {"new": True}
    row.conversation_count += 1
    db.commit()
    return {"new": False}
