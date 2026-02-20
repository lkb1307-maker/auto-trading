from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from src.exchange.base import Candle, PositionSummary


class Signal(str, Enum):
    LONG = "long"
    SHORT = "short"
    HOLD = "hold"


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
