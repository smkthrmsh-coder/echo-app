# Day 01 — Build Log (2026-06-14)

## What Was Built

### Backend (FastAPI + Python 3.11)
- Full project scaffold with `uv` package manager
- Settings system via `pydantic-settings` + `.env`
- **LLM service**: Anthropic Claude provider with JSON-structured emotion analysis and script generation
- **Voice profile pool**: 12 curated ElevenLabs default voices mapped to 10 emotional tones
- **TTS service**: ElevenLabs provider with per-profile voice settings (stability, similarity_boost, style)
- **Ambience service**: ElevenLabs Sound Generation API (AI-generated ambient audio from text prompts)
- **Audio mixer**: pydub + imageio-ffmpeg (no system ffmpeg required); loops, fades, normalizes
- **Speech recognition**: faster-whisper (local, model lazy-loaded on first use)
- **Pipeline orchestrator**: async parallel TTS + ambience, then mix
- **API routes**: `POST /api/generate`, `POST /api/transcribe`, `GET /api/audio/{id}`, `GET /health`
- **Database**: SQLite via SQLAlchemy, `Generation` model, all generations persisted
- **Tests**: 20 unit tests, 20/20 passing
- **Linting**: ruff — 0 errors

### Frontend (Next.js 14 + TypeScript + Tailwind)
- Custom dark UI (`bg-zinc-950`)
- `PromptInput` — text input + mic button + example prompt chips
- `AudioPlayer` — custom play/pause, seek bar, progress with tone-colored accent
- `ExperienceCard` — displays all emotion profile metadata (title, tags, script, ambience, reasoning)
- `EmotionBadge` — colored badge per emotional tone
- `useAudioRecorder` hook — MediaRecorder abstraction (webm/opus)
- API client (`lib/api.ts`) — generateExperience, transcribeAudio, resolveAudioUrl
- TypeScript build: 0 errors; ESLint: 0 errors; Next.js build: successful

## Files Created
- 30+ backend files across app/, services/, tests/
- 8 frontend files (components, hooks, lib, types)
- Startup scripts: `start-backend.sh`, `start-frontend.sh`
- Documentation: architecture, workflows, decisions, progress

## Test Results
- Backend: 20/20 passing
- Frontend: TypeScript + ESLint + build — all clean

## Known Issues / Remaining Work
See `docs/testing/known_issues.md`

## Pending Before First Use
1. Add `ANTHROPIC_API_KEY` to `backend/.env`
2. Run `./start-backend.sh` in one terminal
3. Run `./start-frontend.sh` in another terminal
4. Open http://localhost:3000
