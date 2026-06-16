"""
Shared SSML-style pause-pacing markup, tuned per emotional intention.

Moved out of chat_provider.py so initial-generation (anthropic_provider.py)
can apply the same pacing as chat replies, not just emotional-mode replies.
"""

from __future__ import annotations

import re

INTENTION_PACING: dict[str, dict] = {
    # Slow, spacious — sleep is the slowest of all nine, deliberately longer than peace
    "sleep": {
        "open": "1.8s", "sentence": "1.2s", "comma": "0.6s", "em": "0.9s", "ellipsis": "4.5s",
    },
    "peace": {
        "open": "1.0s", "sentence": "0.7s", "comma": "0.3s", "em": "0.5s", "ellipsis": "3.2s",
    },
    "listen": {
        "open": "1.0s", "sentence": "0.7s", "comma": "0.35s", "em": "0.5s", "ellipsis": "0.8s",
    },
    "comfort": {
        "open": "0.9s", "sentence": "0.6s", "comma": "0.3s", "em": "0.45s", "ellipsis": "0.9s",
    },
    # Neutral / reflective — clarity is deliberately slower than focus
    "clarity": {
        "open": "0.65s", "sentence": "0.5s", "comma": "0.25s", "em": "0.4s", "ellipsis": "0.8s",
    },
    "encouragement": {
        "open": "0.55s", "sentence": "0.42s", "comma": "0.2s", "em": "0.32s", "ellipsis": "0.55s",
    },
    "focus": {
        "open": "0.5s", "sentence": "0.4s", "comma": "0.15s", "em": "0.3s", "ellipsis": "0.5s",
    },
    "confidence": {
        "open": "0.35s", "sentence": "0.28s", "comma": "0.12s", "em": "0.22s", "ellipsis": "0.35s",
    },
    # Energetic — less silence, more momentum; energy is the fastest of all nine
    "motivation": {
        "open": "0.3s", "sentence": "0.25s", "comma": "0.1s", "em": "0.2s", "ellipsis": "0.3s",
    },
    "energy": {
        "open": "0.18s", "sentence": "0.15s", "comma": "0.06s", "em": "0.12s", "ellipsis": "0.2s",
    },
}
DEFAULT_PACING = {
    "open": "0.6s", "sentence": "0.45s", "comma": "0.2s", "em": "0.35s", "ellipsis": "0.55s",
}


def apply_pacing_markup(script: str, intention: str | None = None) -> str:
    """Inject ElevenLabs SSML break tags tuned to the emotional intention."""
    p = INTENTION_PACING.get(intention or "", DEFAULT_PACING)
    marked = f"<break time='{p['open']}'/> " + script
    marked = re.sub(r"\. +", f". <break time='{p['sentence']}'/> ", marked)
    marked = re.sub(r", +", f", <break time='{p['comma']}'/> ", marked)
    marked = re.sub(r" — ", f" <break time='{p['em']}'/> — <break time='{p['comma']}'/> ", marked)
    marked = re.sub(r"\.\.\. +", f"... <break time='{p['ellipsis']}'/> ", marked)
    return marked
