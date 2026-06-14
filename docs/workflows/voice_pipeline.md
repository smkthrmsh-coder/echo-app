# Voice Pipeline Workflow

## Full Flow (Text Input)

1. User types prompt in frontend → `POST /api/generate`
2. Backend checks `ANTHROPIC_API_KEY` is configured
3. `run_pipeline(prompt)` is called in `pipeline.py`
4. **Step 1 — LLM**: Claude receives the prompt + system prompt → returns JSON with emotion profile + narration script
5. **Step 2 — Parallel**:
   - ElevenLabs TTS synthesizes the script with the chosen voice + settings → `{id}_voice.mp3`
   - ElevenLabs SFX generates ambience audio → `{id}_ambience.mp3`
6. **Step 3 — Mix**: pydub overlays voice on ambience, applies volume, fades, normalizes → `{id}_final.mp3`
7. Intermediate files deleted
8. Generation saved to SQLite
9. Response sent: `{ generation_id, audio_url, emotion_profile, duration_seconds }`
10. Frontend renders AudioPlayer + ExperienceCard, plays audio

## Full Flow (Voice Input)

1. User taps mic → browser captures MediaRecorder audio (webm/opus)
2. On stop → `POST /api/transcribe` with audio blob
3. Backend saves to temp file → faster-whisper transcribes → returns `{ text, language, confidence }`
4. Frontend feeds transcript text into `handleGenerate(text)` → same as text flow above

## Audio Mixing Details

```
Voice track:    ████████████████████████████████  (e.g. 45s)
Ambience track: ████████████████                  (22s max from ElevenLabs SFX)
                → looped: ████████████████████████████████████████ (looped to 47s)
                → trimmed: ████████████████████████████████████    (voice len + 2s)
                → fade in 1.5s, fade out 2s
                → overlaid under voice at ambience_volume_db
Final mix:      normalized to prevent clipping
```

## LLM System Prompt Design

Claude is asked to return a single JSON object with no surrounding text. Key fields:
- `tone` — drives voice selection and UI color theming
- `ambience_prompt` — detailed sound description for ElevenLabs SFX (20–40 words)
- `ambience_volume_db` — Claude decides how present the ambience should be (-30 subtle → -8 immersive)
- `script` — 150–250 word narration written for spoken delivery (contractions, natural pauses, sensory language)

Claude's emotional intelligence determines the quality of the experience.
