# Experience OS — Architecture (Sprint 1A + Sprint 2 + Sprint 3)

## Why this exists

Echo has nine emotional "intentions" today (peace, confidence, comfort, motivation, focus,
sleep, energy, clarity, encouragement, listen — plus the bare `default`). The product plan is
to grow this to 50+ "experiences." Hardcoding each one's voice, prompt, and behavior across
`anthropic_provider.py`, `chat_provider.py`, and `voice_mapping.py` does not scale.

This sprint introduces the foundation those future experiences will run on: **Experience OS**
and the **Blueprint** configuration system. It does not change any prompt, voice, journey, or
UI behavior — every blueprint shipped this sprint is a placeholder, and `ExperienceOS` only
wraps the exact code paths that already existed. See "What changed" below for the one true
behavior-adjacent diff.

## Folder structure

```
app/experience_os/
├── schema.py              Blueprint Pydantic schema (16 sections, all default-safe)
├── blueprint_engine.py     BlueprintEngine + get_engine() shared singleton accessor
├── blueprints/             One YAML placeholder per intention + default.yaml
├── context.py              ExperienceContext dataclass — shared state for a turn
├── events.py                RuntimeEvent — lightweight observability record (Sprint 2)
├── validation.py            hard/soft Blueprint validation (Sprint 2)
├── fragments.py              reusable prompt fragment registry (Sprint 3)
├── composer.py               ExperienceComposer — Blueprint -> ComposedPrompt (Sprint 3)
├── interfaces.py           Protocols for the orchestrated services
├── services/
│   ├── voice_service.py        wraps get_voice_for_intention (voice_mapping.py)
│   ├── music_service.py        wraps TONE_AMBIENCE (chat_provider.py)
│   ├── prompt_service.py       renders a ComposedPrompt (or the legacy ternary) into
│   │                           the final system prompt — the only provider-specific step
│   ├── journey_service.py      stub — journeys.py untouched this sprint
│   ├── reflection_service.py   stub — no reflection system exists yet
│   └── speech_service.py       stub — no speech-pace engine exists yet
├── orchestrator.py         ExperienceOS — the coordinator (live in conversations.py)
└── runtime.py                BlueprintRuntime — the Experience Lifecycle executor (Sprint 2,
                             not yet wired into any route)
```

`app/brain/schema.py` (new) holds `MemoryBundle`, the logical separation of memory into
`universal` / `experience` / `session` scopes (see "Memory architecture" below).

## ExperienceOS

`ExperienceOS(db)` is constructed the same way `EchoBrainService(db)` is — a plain
`sqlalchemy.orm.Session`, no FastAPI dependency wiring inside the class itself.

Its one method this sprint, `prepare_experience(user_id, intention) -> ExperienceContext`:
1. Loads the Blueprint for `intention` via `BlueprintEngine` (falls back to `default` if
   missing/invalid).
2. Calls `EchoBrainService.retrieve_context(user_id)` — the **one** public retrieval API
   Blueprints should ever use. No caller should query `BrainMemory` directly.
3. Returns an `ExperienceContext` whose `.brain_context` is exactly the string
   `get_context_for_user()` already produced before this sprint.

`ExperienceOS` orchestrates; it owns no business logic. The actual LLM/TTS pipeline calls
(`run_pipeline`, `run_chat_pipeline`) are unchanged and are not yet called through
`ExperienceOS` — only the brain-context-retrieval step moved.

## Blueprint schema and engine

A `Blueprint` has 16 sections (Identity, EmotionalObjective, PromptInstructions,
RetrievalStrategy, ContextVerification, JourneyStrategy, VoiceConfiguration,
SpeechBehaviour, PauseBehaviour, VocabularyStyle, SentenceStructure,
BackgroundMusicStrategy, ReflectionRules, MemoryUpdateRules, UIBehaviour, Analytics).
Every section has safe defaults, so a near-empty YAML validates.

**Voice IDs are never duplicated into YAML.** A blueprint's `voice_configuration` stores
only `voice_intention: <key>` — a lookup key into `INTENTION_VOICE_MAP` in
`app/services/llm/voice_mapping.py`, which remains the single source of truth for actual
ElevenLabs IDs. `BlueprintEngine.load()` resolves `resolved_male_voice_id`,
`resolved_female_voice_id`, `resolved_stability`, `resolved_similarity_boost`, and
`resolved_style` from that map at load time. If `voice_mapping.py` changes, every blueprint
referencing that intention picks up the change automatically on next process start — no
blueprint file edits needed.

**Caching:** `BlueprintEngine` caches loaded blueprints in an in-memory dict, keyed by slug,
for the lifetime of the process. **There is no file-watch or TTL — changing a YAML file
requires a process restart to take effect.** This is intentional for this sprint; revisit if
Sprint 2+ needs hot-reload for faster iteration.

**Graceful failure:** a missing file, invalid YAML (`yaml.YAMLError`), or schema validation
failure (`pydantic.ValidationError`) logs a warning and falls back to `blueprints/default.yaml`
— `BlueprintEngine.load()` never raises into its caller.

### Adding a new Blueprint

1. Create `app/experience_os/blueprints/<slug>.yaml` with at minimum:
   ```yaml
   identity:
     slug: <slug>
     display_name: <Display Name>
     category: <category>
   voice_configuration:
     voice_intention: <existing key from INTENTION_VOICE_MAP, e.g. comfort>
   ```
2. If the experience needs a brand-new voice (not one of the 10 existing intentions), add it
   to `INTENTION_VOICE_MAP` in `voice_mapping.py` first — do not invent a new ID source.
3. Everything else (prompt instructions, retrieval strategy, journey strategy, reflection
   rules, ...) is schema-defined but **not yet read by any real code path**. Populating those
   fields has no effect until the experience is migrated (see "Migration plan").

## Memory architecture

`EchoBrainService.retrieve_context(user_id) -> MemoryBundle` is the new single public
retrieval API. `MemoryBundle` has three fields:

- **universal** — identity, goals, relationships, preferences, achievements, etc. that apply
  across every experience. This is the only scope populated today; it wraps the existing
  `get_context_for_user()` logic unchanged.
- **experience** — knowledge specific to one Blueprint (e.g. a user's preferred grounding
  exercise for Peace, or preferred bedtime routine for Sleep). Not yet populated — storage and
  extraction for this scope ship in a future sprint.
- **session** — the active conversation's transient context. Not yet populated by Echo Brain;
  the conversation's own message history already serves this role today.

All three scopes currently live in the same `BrainMemory` table — this is a logical
abstraction only, not a storage migration. `get_context_for_user()` is untouched and still
used internally by `retrieve_context()`; nothing that called it before had to change.

## Context verification (designed, not implemented)

The `ContextVerification` schema section exists so a future Blueprint can require Echo to ask
before personalizing around a Brain memory ("I remember you mentioned an interview coming up —
is today's anxiety related to that, or something else?") rather than assuming it. No Blueprint
sets `context_verification.enabled: true` yet, and no code path reads this field yet.

## What changed in existing files (the only behavior-adjacent edits)

- `app/api/routes/conversations.py`: `create_conversation` and `send_message` each replace
  `brain = EchoBrainService(db); brain_context = brain.get_context_for_user(...)` with
  `experience_os = ExperienceOS(db); brain_context = experience_os.prepare_experience(...).brain_context`.
  The string value is identical; see `tests/test_prompt_service.py` and the live smoke test.
- `app/services/llm/anthropic_provider.py` and `chat_provider.py`: the inline
  `(brain_context + "\n\n" + base_prompt) if brain_context else base_prompt` ternary is now a
  call to `DefaultPromptConstructionService.build_system_prompt(...)`, which does exactly the
  same thing.

Everything else — `run_pipeline`, `run_chat_pipeline`, journeys, voice resolution, TTS,
ambience — is untouched.

## Sprint 2 — Blueprint Runtime

Sprint 1A made Blueprints loadable and cached, but nothing executed one end-to-end — Blueprints
were configuration nobody read beyond voice-ID resolution. Sprint 2 builds `BlueprintRuntime`
(`app/experience_os/runtime.py`), the component that runs the full **Experience Lifecycle** for
a Blueprint. It is new, fully tested infrastructure that **receives zero production traffic this
sprint** — `conversations.py`'s two live call sites still go through `ExperienceOS` exactly as
before. A future migration sprint is the first time a real Blueprint drives behavior through this
Runtime in production (see "Migration plan").

### Experience Lifecycle

```
Blueprint Selected
  -> Load Blueprint                  (BlueprintEngine, validated — see "Validation" below)
  -> Retrieve Context from Echo Brain
  -> Build Experience Context
  -> Determine Voice                 (VoiceSelectionService)
  -> Determine Music                 (MusicSelectionService)
  -> Determine Speech Behaviour
  -> Compose Prompt Instructions     (ExperienceComposer — Sprint 3, see below)
  -> Construct Prompt                (PromptConstructionService)
  -> Generate AI Response            (existing run_pipeline / run_chat_pipeline, untouched)
  -> Human Speech Engine + Generate Audio
  -> Update Reflection               (ReflectionService — stub, no-op)
  -> Update Echo Brain               (caller's responsibility — see "Memory" below)
```

`BlueprintRuntime.build_context(...)` covers everything through "Construct Prompt" and returns
an `ExperienceContext`. `execute()` / `execute_reply()` call `build_context()` then delegate to
the existing `run_pipeline()` / `run_chat_pipeline()` — neither of which changed — and append the
remaining lifecycle events.

### ExperienceContext (expanded)

`ExperienceContext` now carries every value a future Runtime stage should need, so later sprints
read from context instead of re-deriving values: `blueprint`, `memories` (`MemoryBundle`),
`conversation_history`, `user_profile`, `journey_state`, `reflection_summary`, `voice_selection`
(`VoiceSelection(voice_id, gender)`), `music_playlist`, `speech_behaviour`, `prompt_instructions`,
`composed_prompt` (`ComposedPrompt | None` — Sprint 3, see below), and `events`
(`list[RuntimeEvent]`). `user_profile` and `journey_state` are typed but unpopulated this sprint —
no `UserProfile` table or journey-state read exists yet to fill them.

### Blueprint execution — Runtime interprets, Blueprints don't act

Blueprints never call a service directly. `BlueprintRuntime` reads a Blueprint's fields and
configures the relevant service on the Blueprint's behalf:

- `voice_configuration` -> `VoiceSelectionService.select_voice(intention, gender_preference)`.
  **Voice selection always uses the original `intention` argument, never the (possibly
  fallen-back) Blueprint's `identity.slug`** — so a validation fallback can never silently change
  what voice a user hears.
- `background_music_strategy.tone_ambience_key` -> `MusicSelectionService.select_ambience(...)`.
- Most prompt-relevant sections (`prompt_instructions`, `emotional_objective`, `speech_behaviour`,
  `vocabulary_style`, `sentence_structure`, `retrieval_strategy`, `reflection_rules`,
  `journey_strategy`) -> `ExperienceComposer.compose(...)`, whose `ComposedPrompt` output, plus
  brain context, then goes to `PromptConstructionService.build_system_prompt(...)` (Sprint 3, see
  below).

None of these resolved values are passed into `run_pipeline`/`run_chat_pipeline` yet — those
pipelines still resolve voice/music/prompt themselves, identically to before. The Runtime
computes and records them for observability and for Sprint 3's migration, not to change today's
output.

### Runtime events

`RuntimeEvent(name, data)` — a plain dataclass, not a pub/sub system. Every lifecycle step
appends one to `ExperienceContext.events`: `BlueprintLoaded`, `ContextRetrieved`, `VoiceSelected`,
`MusicSelected`, `PromptComposed` (Sprint 3 — `data["fragments"]` lists which fragment keys the
Composer selected), `PromptPrepared`, `SpeechGenerated`, `ReflectionUpdated`, `MemoryUpdated`.
`execute()`/`execute_reply()` always emit all 9, even when a step is a no-op stub (e.g.
`ReflectionUpdated.data["applied"]` is `False` until a real reflection system exists), so the
event stream is a complete, inspectable record of one turn for debugging.

### Validation — hard vs. soft

`app/experience_os/validation.py` splits Blueprint problems into two tiers:

- **Hard** (`validate_blueprint`) — only an empty `identity.slug`. This is the one failure mode
  `BlueprintEngine`'s own YAML/schema checks can't catch on their own. `BlueprintRuntime` falls
  back to the `default` Blueprint and records `fallback_from` on the `BlueprintLoaded` event.
- **Soft** (`blueprint_warnings`) — an unmapped `voice_intention` or `tone_ambience_key`. The
  downstream services (`get_voice_for_intention`, `TONE_AMBIENCE.get`) already fall back
  gracefully for these, so the Blueprint is kept as-is; the warning exists only so a Blueprint
  author notices the typo, attached to the `BlueprintLoaded` event's data.

### Performance — no new caching layer

Reasoned, not assumed: voice resolution is already cached as part of the cached `Blueprint`
(`resolved_*` fields computed once at load); `TONE_AMBIENCE` is already a static dict (O(1));
the constructed system prompt depends on per-request `brain_context`, so caching it would serve
stale memory — an actual bug, not an optimization. No additional cache was added this sprint.

### Human Speech, Reflection, Memory — hooks only

- **Speech**: `ExperienceContext.speech_behaviour` snapshots `Blueprint.speech_behaviour` plus
  `HumanSpeechService.is_enabled()` (currently always `False`). No pacing/warmth tuning is
  applied to real audio yet.
- **Reflection**: `ReflectionService.is_enabled()` is always `False`; `_finish()` still emits
  `ReflectionUpdated(applied=False)` so the Runtime is "Blueprint aware" without any real
  reflection logic existing yet.
- **Memory**: `execute()`/`execute_reply()` never call brain extraction themselves — that stays
  exactly where it lives today, in `conversations.py`'s `BackgroundTasks`, scheduled after
  `Message` rows are persisted. `BlueprintRuntime.update_memory(ctx, messages)` exists as a hook
  for a future caller but is not invoked automatically, keeping "memory updates remain
  unchanged" literally true. A `MemoryUpdated(applied=False, reason=...)` event is still emitted
  from `_finish()` for event-stream symmetry.

## Sprint 3 — Experience Composer

Sprint 2's `PromptConstructionService.build_system_prompt` only ever did the brain-context-prepend
ternary — none of a Blueprint's 9 prompt-relevant sections (`prompt_instructions`,
`emotional_objective`, `speech_behaviour`, `pause_behaviour`, `vocabulary_style`,
`sentence_structure`, `retrieval_strategy`, `reflection_rules`, `journey_strategy`) were read by
anything. Sprint 3 builds the **Experience Composer**
(`app/experience_os/composer.py`, `ExperienceComposer`) — the intelligence layer between
`BlueprintRuntime` and `PromptConstructionService` that turns those declarative fields into
structured, model-agnostic prompt instructions. Like Sprint 2, this is zero production risk:
`BlueprintRuntime` still isn't called from any route, and `PromptConstructionService`'s two real
call sites (`anthropic_provider.py`, `chat_provider.py`) keep calling it with 2 positional args, so
the new third `composed` parameter is never populated there — behaviour outside the Runtime is
unchanged.

### Composition pipeline

```
ExperienceContext + Blueprint -> ExperienceComposer.compose() -> ComposedPrompt
  -> PromptConstructionService.build_system_prompt(brain_context, base_prompt, composed)
  -> final system prompt -> LLM
```

`ExperienceComposer` interprets the Blueprint, Echo Brain memory (`ctx.memories`), journey state,
reflection rules, and speech/voice configuration already present on `ExperienceContext`, plus three
inputs unique to composition (`current_message`, `previous_assistant_message`,
`conversation_type`) that `BlueprintRuntime` derives from which method was called —
`execute()` -> `conversation_type="initial"`, `execute_reply()` -> `"reply"` (the only two real entry
points today; this is "which entrypoint," not "turn count").

### ComposedPrompt

A plain dataclass: `conversation_goal`, `primary_emotional_objective`, `conversation_strategy`,
`speech_instructions`, `tone`, `vocabulary`, `sentence_structure`, `conversation_boundaries`,
`memory_usage_rules`, `reflection_rules`, `journey_rules`, `fragments_used`. Two design choices
worth calling out:

- **`tone` is `blueprint.speech_behaviour.warmth`, not `voice_configuration.voice_intention`.**
  `voice_intention` is a TTS voice-routing key into `INTENTION_VOICE_MAP` — reusing it for prompt
  tone would permanently couple voice selection to prompt tone. `speech_behaviour.warmth` is the
  closest existing "delivery tone" concept and was otherwise unused.
- **Absence is always explicit.** When no Echo Brain memory is available,
  `memory_usage_rules` is `["No prior memory is available..."]`, not an empty list — the model is
  always told plainly not to invent details, rather than the gap being silently dropped.

### Fragments — reusable building blocks

`app/experience_os/fragments.py` holds every instruction sentence the Composer can emit
(`FRAGMENTS: dict[str, str]`, keys: empathy, reflection, grounding, motivation, silence, safety,
memory, journey, plus 3 composer-internal ones: `memory_absent`, `conversation_initial`,
`conversation_reply`). `composer.py` never hardcodes instruction text inline — it only selects,
prioritizes, and truncates. `INTENTION_DEFAULT_FRAGMENTS` maps each of the 10 existing intentions
to 1-2 of the 8 conceptual fragments (e.g. `peace` -> grounding+silence, `motivation` -> motivation)
— a deliberately simple v1 heuristic, the natural place a future "Adaptive Prompting" system would
plug in a learned policy instead.

### Context prioritization

`conversation_strategy` is built from priority-ordered candidate tiers (highest first): current
conversation > Echo Brain memory > journey state > reflection > user profile (no-op today — no
`UserProfile` data exists yet) > explicit Blueprint `style_notes` > generic intention-default
fragments. Candidates are deduplicated by exact text, then truncated to
`MAX_CONVERSATION_STRATEGY_LINES = 4` (a named, tunable constant) so the prompt isn't overwhelmed
with every applicable fragment at once — higher-priority tiers always survive truncation before
lower ones. `fragments_used` records which fragment keys made the final cut, attached to the
`PromptComposed` event for observability.

### Model-agnostic design and future extensibility

`ExperienceComposer.compose()` is pure (deterministic, no LLM calls, no randomness) — identical
input always produces an identical `ComposedPrompt`, which is what makes "prompt stability"
possible and is also the reason future **Dynamic Experience Blending** and **Adaptive Prompting**
must be implemented as steps *before* `compose()` is called (merging multiple Blueprints into one
synthetic Blueprint, or mutating the effective `ExperienceContext`/Blueprint inputs from
accumulated history) rather than inside the Composer itself. `PromptConstructionService` remains
the only place doing provider-specific formatting; today there's only one rendering style since
both LLM providers consume a flat system-prompt string.

## Migration plan (future sprints)

`ExperienceOS`, `BlueprintEngine`, `BlueprintRuntime`, and now `ExperienceComposer` exist so future
sprints can migrate one experience at a time onto a real Blueprint (populating
`prompt_instructions`, `journey_strategy`, `reflection_rules`, etc., and having `conversations.py`
call `BlueprintRuntime.execute()`/`execute_reply()` instead of `run_pipeline`/`run_chat_pipeline`
directly) without a big-bang rewrite. No experience has been migrated yet — Peace's migration is
still pending a future sprint:

- Peace
- Confidence
- Comfort
- Better Sleep
- remaining experiences

Each migration sprint should: populate the real fields on that experience's Blueprint YAML,
make the relevant service (`PromptConstructionService`, `JourneyService`, ...) actually read
from the Blueprint instead of falling back to legacy logic, switch that intention's
`conversations.py` call site to `BlueprintRuntime`, and verify no regression for every other
intention (which still falls through to legacy behavior until its own migration sprint).
