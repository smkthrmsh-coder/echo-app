# Known Issues & Testing Notes

## Known Issues

### KI-001 — ANTHROPIC_API_KEY not configured
**Status:** Pending user action  
**Impact:** `/api/generate` returns HTTP 503  
**Fix:** Add key to `backend/.env` line: `ANTHROPIC_API_KEY=sk-ant-...`

### KI-002 — First Whisper transcription is slow (~3–8s)
**Status:** Acceptable for MVP  
**Cause:** `faster-whisper` loads the model into memory on the first call (lazy-loaded + cached)  
**Workaround:** Subsequent transcriptions are fast. Pre-warm by sending a dummy request if desired.

### KI-003 — ElevenLabs SFX max 22s per request
**Status:** Mitigated  
**Cause:** ElevenLabs Sound Generation API caps at 22 seconds per request  
**Mitigation:** The mixer loops the ambience to match full voice duration. Short voice files (under 22s) get unlooped ambience. Long files (over 22s) get seamless looping.

### KI-004 — pydub import-time warning about ffmpeg
**Status:** Cosmetic only  
**Cause:** pydub's utils.py checks for ffmpeg at import time before our `mixer.py` patches the path  
**Impact:** Warning appears in logs but ffmpeg is correctly configured when mixing actually runs

### KI-005 — Audio files accumulate in backend/tmp/audio/
**Status:** Acceptable for MVP  
**Cause:** Final mixed files are kept for serving via `/api/audio/{id}`  
**Future:** Add a cleanup job to delete files older than N days

### KI-006 — Mic input requires HTTPS in production browsers
**Status:** Non-issue for local development  
**Cause:** Browser MediaRecorder API requires a secure context (HTTPS) in production  
**MVP:** localhost is always treated as secure — no issue locally

## Test Coverage

| Area | Coverage | Notes |
|---|---|---|
| EmotionProfile models | ✅ Full | All tones, voice mappings, defaults |
| Voice pool | ✅ Full | 12 voices, tone→voice mapping, gender preference |
| LLM JSON parser | ✅ Full | Plain JSON, markdown fenced, invalid, unknown tones, clamping |
| API routes | ✅ Smoke | health, 503 without key, 422 validation, 404 audio |
| Audio mixer | ❌ Not tested | Requires actual audio files — integration test only |
| TTS provider | ❌ Not tested | Requires live ElevenLabs API |
| Ambience provider | ❌ Not tested | Requires live ElevenLabs API |
| Frontend components | ❌ Not tested | No React test runner configured |

## Future Test Improvements
- Add integration test that mocks ElevenLabs responses with real audio fixtures
- Add Playwright e2e test for the frontend flow
- Add React Testing Library for component unit tests
