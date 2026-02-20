from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.exchange.base import Candle
from src.strategy.base import Signal
from src.strategy.ema_cross import EmaCrossConfig, EmaCrossStrategy


def _candles_from_closes(closes: list[Decimal]) -> list[Candle]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)  # noqa: UP017
    candles: list[Candle] = []
    for idx, close in enumerate(closes):
        open_time = start + timedelta(hours=idx)
        close_time = open_time + timedelta(hours=1)
        candles.append(
            Candle(
                open_time=open_time,
                close_time=close_time,
                open_price=close,
                high_price=close,
                low_price=close,
                close_price=close,
                volume=Decimal("1"),
            )
        )
    return candles


def test_generate_long_on_upward_crossover() -> None:
    closes = [Decimal("10")] * 8 + [Decimal("8"), Decimal("16")]
    strategy = EmaCrossStrategy(EmaCrossConfig(fast_period=3, slow_period=5))

    decision = strategy.generate(_candles_from_closes(closes))

    assert decision.signal is Signal.LONG
    assert "crossed above" in decision.reason


def test_generate_short_on_downward_crossover() -> None:
    closes = [Decimal("10")] * 8 + [Decimal("12"), Decimal("4")]
    strategy = EmaCrossStrategy(EmaCrossConfig(fast_period=3, slow_period=5))

    decision = strategy.generate(_candles_from_closes(closes))

    assert decision.signal is Signal.SHORT
    assert "crossed below" in decision.reason


def test_generate_hold_when_no_crossover() -> None:
    closes = [Decimal("10")] * 12
    strategy = EmaCrossStrategy(EmaCrossConfig(fast_period=3, slow_period=5))

    decision = strategy.generate(_candles_from_closes(closes))

    assert decision.signal is Signal.HOLD
    assert decision.reason == "no EMA crossover on latest candle close"
