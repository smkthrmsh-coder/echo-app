"""
RuntimeEvent — lightweight observability record for BlueprintRuntime.

Not a pub/sub system. Events are simply collected on ExperienceContext.events
and logged at debug level as they happen, so a single request's full lifecycle
can be inspected after the fact without instrumenting every call site by hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeEvent:
    name: str
    data: dict[str, Any] = field(default_factory=dict)
