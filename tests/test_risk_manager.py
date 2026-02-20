from __future__ import annotations

from datetime import UTC, datetime

from src.app.state import BotState
from src.app.types import Signal
from src.config.settings import Settings
from src.risk.risk_manager import RiskManager
from src.strategy.base import SignalDecision


def _decision(signal: Signal) -> SignalDecision:
    return SignalDecision(
        signal=signal,
        reason="test",
        timestamp=datetime.now(UTC),
    )


def test_blocks_when_trades_today_hits_daily_limit() -> None:
    settings = Settings(max_trades_per_day=2)
    state = BotState(trades_today=2)

    decision = RiskManager().evaluate(settings, state, None, _decision(Signal.LONG))

    assert decision.allow is False
    assert decision.severity == "BLOCK"
    assert "Max trades per day reached" in decision.reason


def test_blocks_when_daily_profit_stop_reached() -> None:
    settings = Settings(daily_profit_stop_pct=5.0)
    state = BotState(day_pnl_pct=5.0)

    decision = RiskManager().evaluate(settings, state, None, _decision(Signal.LONG))

    assert decision.allow is False
    assert decision.severity == "BLOCK"
    assert "Daily profit stop reached" in decision.reason


def test_blocks_when_daily_loss_stop_reached() -> None:
    settings = Settings(daily_loss_stop_pct=-3.0)
    state = BotState(day_pnl_pct=-3.0)

    decision = RiskManager().evaluate(settings, state, None, _decision(Signal.SHORT))

    assert decision.allow is False
    assert decision.severity == "BLOCK"
    assert "Daily loss stop reached" in decision.reason


def test_hold_signal_returns_info_and_disallow() -> None:
    settings = Settings()
    state = BotState()

    decision = RiskManager().evaluate(settings, state, None, _decision(Signal.HOLD))

    assert decision.allow is False
    assert decision.severity == "INFO"
    assert decision.reason == "HOLD signal"


def test_allows_normal_trade_when_limits_not_hit() -> None:
    settings = Settings(
        max_trades_per_day=20,
        daily_profit_stop_pct=5.0,
        daily_loss_stop_pct=-3.0,
    )
    state = BotState(trades_today=1, day_pnl_pct=0.5)

    decision = RiskManager().evaluate(settings, state, None, _decision(Signal.LONG))

    assert decision.allow is True
    assert decision.severity == "INFO"
    assert decision.reason == "Risk checks passed"
