# Decision Log

## DEC-001 — ffmpeg via imageio-ffmpeg (not system install)
**Date:** 2026-06-14  
**Problem:** User has no Homebrew and no system ffmpeg, required by pydub for MP3 encode/decode.  
**Decision:** Use `imageio-ffmpeg` which bundles a static ffmpeg binary. Patch pydub's converter path at import time in `mixer.py`.  
**Why:** Zero user setup. Works on any macOS without admin rights. Fully self-contained.

## DEC-002 — Ambience via ElevenLabs SFX API (not bundled files)
**Date:** 2026-06-14  
**Problem:** Need background ambient audio that matches the emotional context dynamically.  
**Decision:** Use ElevenLabs Sound Generation API (`POST /v1/sound-generation`). Same API key as TTS.  
**Trade-off:** Requires internet for every generation. Dynamic prompts mean better contextual matching than pre-bundled files.  
**Why:** User explicitly chose this option. More immersive than static loops.

## DEC-003 — Voice selection via pre-mapped pool (not live API lookup)
**Date:** 2026-06-14  
**Problem:** ElevenLabs has 100+ voices. Dynamic lookup per request would be slow and fragile.  
**Decision:** Maintain a curated pool of 12 stable ElevenLabs default voices in `voice_profiles.py`, mapped to emotional archetypes. Claude selects tone → pool selects voice.  
**Why:** Fast, predictable, no additional API calls. Voices are stable ElevenLabs defaults available on all plans.

## DEC-004 — TTS + Ambience generated in parallel (asyncio.gather)
**Date:** 2026-06-14  
**Problem:** Sequential TTS then ambience would double latency.  
**Decision:** Run TTS synthesis and ambience generation concurrently via `asyncio.gather` in `pipeline.py`.  
**Why:** Both calls are independent I/O. Reduces total pipeline latency by ~40–50%.

## DEC-005 — Intermediate audio files cleaned up after mixing
**Date:** 2026-06-14  
**Problem:** voice.mp3 and ambience.mp3 are only needed to produce final.mp3. Keeping them wastes disk.  
**Decision:** Delete voice and ambience files after mixing succeeds in `pipeline.py`.  
**Why:** Only the final mixed file is served. Clean disk = easier debugging.

## DEC-006 — Whisper model lazy-loaded with lru_cache
**Date:** 2026-06-14  
**Problem:** Loading the Whisper model takes ~2–5s. Loading it per request would be unusable.  
**Decision:** Load model once on first transcription request, cache with `@lru_cache(maxsize=1)`.  
**Why:** Subsequent transcriptions are instant. First transcription is slow but acceptable.

## DEC-007 — ANTHROPIC_API_KEY left as placeholder
**Date:** 2026-06-14  
**Problem:** User confirmed they use Anthropic Claude but did not supply the API key during the build session.  
**Resolution:** Added placeholder `YOUR_ANTHROPIC_API_KEY_HERE` in `backend/.env`. The `/generate` endpoint returns HTTP 503 with a clear message if the key is missing. User must fill this in before first use.
