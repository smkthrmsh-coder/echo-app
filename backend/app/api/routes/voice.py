import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import Generation
from app.models.requests import (
    EmotionProfileOut,
    GenerateRequest,
    GenerateResponse,
    TranscribeResponse,
    VoiceSettingsOut,
)
from app.services.emotion.pipeline import run_pipeline
from app.services.speech_recognition.whisper_provider import WhisperProvider

router = APIRouter()
logger = get_logger(__name__)
_whisper = WhisperProvider()


@router.post("/generate", response_model=GenerateResponse, tags=["voice"])
async def generate(
    request: GenerateRequest,
    db: Session = Depends(get_db),
) -> GenerateResponse:
    settings = get_settings()

    _sentinel = "YOUR_ANTHROPIC_API_KEY_HERE"
    if not settings.anthropic_api_key or settings.anthropic_api_key == _sentinel:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured. Please add it to backend/.env",
        )

    try:
        profile, audio_path, duration = await run_pipeline(request.prompt)
    except Exception as exc:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    generation_id = Path(audio_path).stem.replace("_final", "")

    # Persist to DB
    row = Generation(
        id=generation_id,
        session_id=request.session_id,
        prompt=request.prompt,
        experience_title=profile.experience_title,
        tone=profile.tone.value,
        narration_style=profile.narration_style.value,
        pacing=profile.pacing.value,
        voice_id=profile.voice_id,
        voice_name=profile.voice_name,
        ambience_prompt=profile.ambience_prompt,
        music_category=profile.music_category,
        script=profile.script,
        audio_path=audio_path,
        duration_seconds=duration,
    )
    db.add(row)
    db.commit()

    return GenerateResponse(
        generation_id=generation_id,
        audio_url=f"/api/audio/{generation_id}",
        emotion_profile=EmotionProfileOut(
            tone=profile.tone.value,
            narration_style=profile.narration_style.value,
            pacing=profile.pacing.value,
            experience_title=profile.experience_title,
            voice_id=profile.voice_id,
            voice_name=profile.voice_name,
            voice_settings=VoiceSettingsOut(
                stability=profile.voice_settings.stability,
                similarity_boost=profile.voice_settings.similarity_boost,
                style=profile.voice_settings.style,
                use_speaker_boost=profile.voice_settings.use_speaker_boost,
            ),
            ambience_prompt=profile.ambience_prompt,
            music_category=profile.music_category,
            script=profile.script,
            reasoning=profile.reasoning,
        ),
        duration_seconds=duration,
        prompt=request.prompt,
    )


@router.post("/transcribe", response_model=TranscribeResponse, tags=["voice"])
async def transcribe(audio: UploadFile = File(...)) -> TranscribeResponse:
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        result = await _whisper.transcribe(tmp_path)
    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return TranscribeResponse(
        text=result.text,
        confidence=result.confidence,
        language=result.language,
    )


@router.get("/audio/{generation_id}", tags=["voice"])
async def get_audio(generation_id: str, db: Session = Depends(get_db)):
    row = db.query(Generation).filter(Generation.id == generation_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Generation not found")

    if not Path(row.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        path=row.audio_path,
        media_type="audio/mpeg",
        filename=f"{generation_id}.mp3",
    )
