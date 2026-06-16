"""
JourneyService — interface stub only.

journeys.py keeps its current implementation untouched this sprint. Wrapping its
private route-level helpers here would be a layering violation for a service
nothing calls yet; that wiring is deferred to the journeys-migration sprint.
"""

from __future__ import annotations


class DefaultJourneyService:
    def is_enabled(self) -> bool:
        return False
