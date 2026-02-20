from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .types import PositionSummary


@dataclass(slots=True)
class BotState:
    """In-memory mutable state with safe defaults for skeleton mode."""

    started_at: datetime = field(default_factory=datetime.utcnow)
    last_tick_at: datetime | None = None
    tick_count: int = 0
    positions: dict[str, PositionSummary] = field(default_factory=dict)

    def mark_tick(self) -> None:
        self.tick_count += 1
        self.last_tick_at = datetime.utcnow()
