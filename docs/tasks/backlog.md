# Backlog

## High Priority
- [ ] Add ANTHROPIC_API_KEY to backend/.env (user action required)
- [ ] Integration test: full pipeline with real API keys
- [ ] Audio cleanup job for old files in tmp/audio/

## Medium Priority
- [ ] Session history persistence across page reloads (localStorage or cookie)
- [ ] Add more voice providers (OpenAI TTS, Google TTS)
- [ ] Add more LLM providers (OpenAI GPT-4o)
- [ ] Voice cloning support (ElevenLabs instant voice clone)
- [ ] Waveform visualization in AudioPlayer (Web Audio API)
- [ ] Streaming audio response (start playing before mixing is complete)

## Low Priority / Future
- [ ] Multilingual support (Whisper already handles it; need multilingual ElevenLabs voices)
- [ ] Mobile-responsive UI improvements
- [ ] Save favorite experiences
- [ ] Share experience (export audio file)
- [ ] Fine-tune ambience prompts per tone (e.g. curated preset prompts per emotional category)
- [ ] Rate limiting / usage tracking
- [ ] Docker Compose for single-command startup
