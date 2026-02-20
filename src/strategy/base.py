from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.app.types import Signal
from src.exchange.base import Candle, PositionSummary


@dataclass(frozen=True, slots=True)
class SignalDecision:
    signal: Signal
    reason: str
    timestamp: datetime
    confidence: float | None = None


class Strategy(Protocol):
    def generate(
        self,
        candles: list[Candle],
        position: PositionSummary | None = None,
    ) -> SignalDecision: ...
