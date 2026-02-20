from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from src.exchange.base import Candle, PositionSummary
from src.strategy.base import Signal, SignalDecision, Strategy

UTC = getattr(dt, "UTC", dt.timezone(dt.timedelta(0)))


@dataclass(frozen=True, slots=True)
class EmaCrossConfig:
    fast_period: int = 9
    slow_period: int = 21
    min_candles: int | None = None

    def __post_init__(self) -> None:
        if self.fast_period <= 0 or self.slow_period <= 0:
            raise ValueError("EMA periods must be positive")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period")


class EmaCrossStrategy(Strategy):
    def __init__(self, config: EmaCrossConfig | None = None) -> None:
        self.config = config or EmaCrossConfig()
        self.min_candles = self.config.min_candles or (self.config.slow_period + 5)

    def generate(
        self,
        candles: list[Candle],
        position: PositionSummary | None = None,
    ) -> SignalDecision:
        del position

        if len(candles) < self.min_candles:
            fallback_time = candles[-1].close_time if candles else dt.datetime.now(UTC)
            return SignalDecision(
                signal=Signal.HOLD,
                reason=(
                    f"insufficient candles: need {self.min_candles}, got {len(candles)}"
                ),
                timestamp=fallback_time,
            )

        closes = [candle.close_price for candle in candles]
        fast_ema = _ema_series(closes, self.config.fast_period)
        slow_ema = _ema_series(closes, self.config.slow_period)

        prev_fast = fast_ema[-2]
        prev_slow = slow_ema[-2]
        last_fast = fast_ema[-1]
        last_slow = slow_ema[-1]
        timestamp = candles[-1].close_time

        if prev_fast <= prev_slow and last_fast > last_slow:
            return SignalDecision(
                signal=Signal.LONG,
                reason=(
                    "fast EMA crossed above slow EMA "
                    f"({self.config.fast_period}>{self.config.slow_period})"
                ),
                timestamp=timestamp,
            )

        if prev_fast >= prev_slow and last_fast < last_slow:
            return SignalDecision(
                signal=Signal.SHORT,
                reason=(
                    "fast EMA crossed below slow EMA "
                    f"({self.config.fast_period}<{self.config.slow_period})"
                ),
                timestamp=timestamp,
            )

        return SignalDecision(
            signal=Signal.HOLD,
            reason="no EMA crossover on latest candle close",
            timestamp=timestamp,
        )


def _ema_series(values: list[Decimal], period: int) -> list[Decimal]:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        raise ValueError("not enough values to compute EMA")

    multiplier = Decimal("2") / Decimal(period + 1)
    seed = sum(values[:period]) / Decimal(period)
    ema_values: list[Decimal] = [seed]

    for value in values[period:]:
        next_ema = (value - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(next_ema)

    prefix = [seed] * (period - 1)
    return prefix + ema_values
