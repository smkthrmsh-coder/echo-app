"""
BlueprintRuntime — executes the Experience Lifecycle for a Blueprint.

Lifecycle (build_context covers steps 1-7, execute/execute_reply cover the rest):
  1. Load Blueprint
  2. Retrieve Context from Echo Brain
  3. Determine Voice
  4. Determine Music
  5. Determine Speech Behaviour
  6. Compose Prompt Instructions (ExperienceComposer — interprets the Blueprint +
     context into structured, model-agnostic instructions)
  7. Construct Prompt (PromptConstructionService — renders composed instructions
     into the final system prompt; the only provider-specific formatting step)
  8. Generate AI Response + Audio (existing run_pipeline/run_chat_pipeline, untouched)
  9. Update Reflection
  10. Update Echo Brain

It is not called from any route yet, and none of the values it computes
(voice/music/prompt/speech) override what the existing pipelines already
produce on their own. A future migration sprint is the first time a real
Blueprint drives behaviour through this Runtime in production.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.brain.service import EchoBrainService
from app.core.logging import get_logger
from app.models.emotion import EmotionProfile
from app.services.emotion.chat_pipeline import run_chat_pipeline
from app.services.emotion.pipeline import run_pipeline
from app.services.llm.conversation_summarizer import get_conversation_summary_block

from .blueprint_engine import get_engine
from .composer import ExperienceComposer
from .context import ExperienceContext, VoiceSelection
from .events import RuntimeEvent
from .services.journey_service import DefaultJourneyService
from .services.music_service import DefaultMusicSelectionService
from .services.prompt_service import DefaultPromptConstructionService
from .services.reflection_service import DefaultReflectionService
from .services.speech_service import DefaultHumanSpeechService
from .services.voice_service import DefaultVoiceSelectionService
from .validation import blueprint_warnings, validate_blueprint

logger = get_logger(__name__)


@dataclass
class Experience:
    context: ExperienceContext
    profile: EmotionProfile
    audio_path: str
    duration_seconds: float


class BlueprintRuntime:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.brain = EchoBrainService(db)
        self.blueprint_engine = get_engine()
        self.voice_service = DefaultVoiceSelectionService()
        self.music_service = DefaultMusicSelectionService()
        self.prompt_service = DefaultPromptConstructionService()
        self.journey_service = DefaultJourneyService()
        self.reflection_service = DefaultReflectionService()
        self.speech_service = DefaultHumanSpeechService()
        self.composer = ExperienceComposer()

    def build_context(
        self,
        user_id: str,
        intention: str | None,
        base_prompt: str = "",
        gender_preference: str | None = None,
        tone: str | None = None,
        conversation_history: list[dict] | None = None,
        current_message: str | None = None,
        conversation_type: str = "initial",
        conversation_id: str | None = None,
    ) -> ExperienceContext:
        blueprint = self.blueprint_engine.load(intention)
        fallback_from = None
        if validate_blueprint(blueprint):
            fallback_from = blueprint.identity.slug or intention
            logger.warning(f"Blueprint '{fallback_from}' failed validation — falling back")
            blueprint = self.blueprint_engine.load("default")

        warnings = blueprint_warnings(blueprint)
        loaded_data = {"slug": blueprint.identity.slug, "warnings": warnings}
        if fallback_from is not None:
            loaded_data["fallback_from"] = fallback_from
        events = [RuntimeEvent("BlueprintLoaded", loaded_data)]

        bundle = self.brain.retrieve_context(user_id)
        summary_block = get_conversation_summary_block(self.db, conversation_id)
        combined_context = "\n\n".join(p for p in [bundle.universal, summary_block] if p)
        events.append(RuntimeEvent("ContextRetrieved", {"has_memory": bool(bundle.universal)}))

        # Voice selection must always key off the original `intention`, never the
        # (possibly fallen-back) blueprint's slug — otherwise a fallback would
        # silently change the voice a user hears, which is a behaviour change.
        voice_id, gender = self.voice_service.select_voice(intention, gender_preference)
        events.append(RuntimeEvent("VoiceSelected", {"voice_id": voice_id, "gender": gender}))

        ambience_key = tone or blueprint.background_music_strategy.tone_ambience_key or ""
        playlist = self.music_service.select_ambience(ambience_key)
        events.append(RuntimeEvent("MusicSelected", {"playlist": playlist}))

        speech_behaviour = {
            "pacing": blueprint.speech_behaviour.pacing,
            "warmth": blueprint.speech_behaviour.warmth,
            "energy": blueprint.speech_behaviour.energy,
            "fillers_allowed": blueprint.speech_behaviour.fillers_allowed,
            "runtime_driven": self.speech_service.is_enabled(),
        }

        ctx = ExperienceContext(
            user_id=user_id,
            intention=intention,
            blueprint=blueprint,
            brain_context=combined_context,
            memories=bundle,
            conversation_history=conversation_history or [],
            voice_selection=VoiceSelection(voice_id=voice_id, gender=gender),
            music_playlist=playlist,
            speech_behaviour=speech_behaviour,
            events=events,
        )

        previous_assistant_message = next(
            (
                m.get("content")
                for m in reversed(ctx.conversation_history)
                if m.get("role") == "assistant"
            ),
            None,
        )
        composed = self.composer.compose(
            ctx, current_message, previous_assistant_message, conversation_type
        )
        ctx.composed_prompt = composed
        events.append(RuntimeEvent("PromptComposed", {"fragments": composed.fragments_used}))

        ctx.prompt_instructions = self.prompt_service.build_system_prompt(
            combined_context, base_prompt, composed
        )
        events.append(RuntimeEvent("PromptPrepared", {"length": len(ctx.prompt_instructions)}))

        return ctx

    async def execute(
        self,
        user_id: str,
        prompt: str,
        intention: str | None = None,
        celebrity_voice_id: str | None = None,
        gender: str | None = None,
        speaking_styles: list[str] | None = None,
        username: str = "there",
    ) -> Experience:
        ctx = self.build_context(
            user_id,
            intention,
            gender_preference=gender,
            current_message=prompt,
            conversation_type="initial",
        )
        profile, audio_path, duration = await run_pipeline(
            prompt,
            celebrity_voice_id=celebrity_voice_id,
            gender=gender,
            speaking_styles=speaking_styles,
            username=username,
            intention=intention,
            brain_context=ctx.brain_context or None,
            composed_prompt=ctx.composed_prompt,
            pause_behaviour_enabled=ctx.blueprint.pause_behaviour.enabled,
        )
        self._finish(ctx, audio_path, duration)
        return Experience(
            context=ctx, profile=profile, audio_path=audio_path, duration_seconds=duration
        )

    async def execute_reply(
        self,
        user_id: str,
        user_message: str,
        history: list[dict],
        speaking_styles: list[str],
        gender: str,
        energy_level: int,
        intention: str | None = None,
        emotional_mode: bool = False,
        celebrity_voice_id: str | None = None,
        locked_voice_id: str | None = None,
        locked_voice_name: str | None = None,
        conversation_id: str | None = None,
    ) -> Experience:
        ctx = self.build_context(
            user_id,
            intention,
            gender_preference=gender,
            conversation_history=history,
            current_message=user_message,
            conversation_type="reply",
            conversation_id=conversation_id,
        )
        profile, audio_path, duration = await run_chat_pipeline(
            user_message=user_message,
            history=history,
            speaking_styles=speaking_styles,
            gender=gender,
            energy_level=energy_level,
            emotional_mode=emotional_mode,
            celebrity_voice_id=celebrity_voice_id,
            locked_voice_id=locked_voice_id,
            locked_voice_name=locked_voice_name,
            intention=intention,
            brain_context=ctx.brain_context or None,
            composed_prompt=ctx.composed_prompt,
            pause_behaviour_enabled=ctx.blueprint.pause_behaviour.enabled,
        )
        self._finish(ctx, audio_path, duration)
        return Experience(
            context=ctx, profile=profile, audio_path=audio_path, duration_seconds=duration
        )

    def _finish(self, ctx: ExperienceContext, audio_path: str, duration: float) -> None:
        ctx.events.append(RuntimeEvent(
            "SpeechGenerated", {"audio_path": audio_path, "duration_seconds": duration}
        ))
        applied = self.reflection_service.is_enabled()
        ctx.events.append(RuntimeEvent("ReflectionUpdated", {"applied": applied}))
        # Real persistence stays with the caller (conversations.py owns the
        # BackgroundTasks scheduling) — this event exists only for symmetry so
        # the event stream always reflects all 9 lifecycle events.
        ctx.events.append(RuntimeEvent(
            "MemoryUpdated", {"applied": False, "reason": "not yet wired — caller owns persistence"}
        ))

    async def update_memory(self, ctx: ExperienceContext, messages: list[dict]) -> None:
        """Exposed for future callers; not invoked automatically by execute()/execute_reply()."""
        await self.brain.extract_from_conversation(ctx.user_id, messages)
        ctx.events.append(RuntimeEvent("MemoryUpdated", {"applied": True}))
