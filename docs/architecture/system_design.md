# System Design — Voice Emotion App

## Overview

A local-first AI voice companion that transforms emotional prompts into immersive audio experiences. The system generates a complete emotional profile (tone, voice, pacing, ambience) and produces a mixed audio file combining AI-generated speech with dynamically generated ambient sound.

---

## Request Pipeline

```
User Prompt (text or voice)
        │
        ▼
[Speech Recognition — Whisper]     ← only if voice input
        │
        ▼
[LLM — Anthropic Claude]
  • Analyzes emotional intent
  • Selects tone, pacing, narration style
  • Maps to voice profile (ElevenLabs voice ID + settings)
  • Designs ambience sound prompt
  • Writes narration script (150–250 words)
        │
        ├──────────────────────────┐
        ▼                          ▼
[TTS — ElevenLabs]         [Ambience — ElevenLabs SFX API]
  voice.mp3                  ambience.mp3 (up to 22s)
        │                          │
        └──────────┬───────────────┘
                   ▼
          [Audio Mixer — pydub]
            • Applies volume levels
            • Loops ambience to match voice length
            • Fades in/out ambience
            • Normalizes final mix
                   │
                   ▼
            final_{id}.mp3
                   │
                   ▼
          [HTTP Response → Frontend]
            audio_url + emotion_profile metadata
```

---

## Component Map

| Component | Location | Responsibility |
|---|---|---|
| FastAPI app | `backend/app/main.py` | Entry point, CORS, lifespan |
| Config | `backend/app/core/config.py` | Settings via pydantic-settings + .env |
| LLM base | `backend/app/services/llm/base.py` | Provider ABC |
| Anthropic provider | `backend/app/services/llm/anthropic_provider.py` | Claude integration |
| Voice profiles | `backend/app/services/llm/voice_profiles.py` | Voice pool + tone→voice mapping |
| TTS base | `backend/app/services/tts/base.py` | Provider ABC |
| ElevenLabs TTS | `backend/app/services/tts/elevenlabs_provider.py` | TTS synthesis |
| Ambience base | `backend/app/services/ambience/base.py` | Provider ABC |
| ElevenLabs SFX | `backend/app/services/ambience/elevenlabs_provider.py` | Sound effects generation |
| Audio mixer | `backend/app/services/audio/mixer.py` | pydub mixing + imageio-ffmpeg |
| Pipeline | `backend/app/services/emotion/pipeline.py` | Orchestrates full flow |
| Whisper | `backend/app/services/speech_recognition/whisper_provider.py` | Local STT |
| DB models | `backend/app/db/models.py` | SQLite/SQLAlchemy |
| API routes | `backend/app/api/routes/voice.py` | /generate /transcribe /audio/{id} |
| Frontend page | `frontend/app/page.tsx` | Main React UI |
| PromptInput | `frontend/components/PromptInput.tsx` | Text + mic input |
| AudioPlayer | `frontend/components/AudioPlayer.tsx` | Custom audio player |
| ExperienceCard | `frontend/components/ExperienceCard.tsx` | Emotion profile display |
| API client | `frontend/lib/api.ts` | fetch wrappers |
| Recorder hook | `frontend/hooks/useAudioRecorder.ts` | MediaRecorder abstraction |

---

## Data Models

### EmotionProfile (backend/app/models/emotion.py)
- `tone: EmotionalTone` — energetic | calm | fierce | comforting | melancholic | playful | mysterious | romantic | anxious | hopeful
- `narration_style: NarrationStyle` — coach | narrator | whisper | storyteller | friend | guide
- `pacing: Pacing` — fast | medium | slow | very_slow
- `voice_id, voice_name` — ElevenLabs voice
- `voice_settings` — stability, similarity_boost, style, use_speaker_boost
- `ambience_prompt` — text prompt for ElevenLabs SFX
- `ambience_volume_db` — float, range [-30, -8]
- `script` — generated narration text

### Generation (DB model)
Persists every generation for history and audio retrieval.

---

## Technology Decisions

| Decision | Choice | Reason |
|---|---|---|
| Backend framework | FastAPI | Async, fast, great for I/O-heavy pipelines |
| LLM | Anthropic Claude (sonnet-4-6) | Best instruction following for structured JSON output |
| TTS | ElevenLabs | Best emotional voice quality available |
| Ambience | ElevenLabs SFX API | Dynamic, AI-generated, same key as TTS |
| STT | faster-whisper (local) | No cloud dependency, no extra API key |
| Audio mixing | pydub + imageio-ffmpeg | No system ffmpeg required |
| DB | SQLite | Zero infra, local-first, sufficient for MVP |
| Frontend | Next.js 14 + TypeScript + Tailwind | Standard, well-documented, fast to iterate |
| Package mgr (BE) | uv | Fast, modern, lock-file based |
