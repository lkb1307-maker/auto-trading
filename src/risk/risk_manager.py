from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.app.state import BotState
from src.app.types import PositionSummary, Signal
from src.config.settings import Settings
from src.strategy.base import SignalDecision

Severity = Literal["INFO", "WARN", "BLOCK"]


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allow: bool
    reason: str
    severity: Severity


class RiskManager:
    """Pure risk evaluator for strategy decisions."""

    def evaluate(
        self,
        settings: Settings,
        state: BotState,
        position: PositionSummary | None,
        signal_decision: SignalDecision,
    ) -> RiskDecision:
        _ = position

        if signal_decision.signal == Signal.HOLD:
            return RiskDecision(allow=False, reason="HOLD signal", severity="INFO")

        if state.trades_today >= settings.max_trades_per_day:
            return RiskDecision(
                allow=False,
                reason=(
                    "Max trades per day reached: "
                    f"{state.trades_today}/{settings.max_trades_per_day}"
                ),
                severity="BLOCK",
            )

        if state.day_pnl_pct >= settings.daily_profit_stop_pct:
            return RiskDecision(
                allow=False,
                reason=(
                    "Daily profit stop reached: "
                    f"{state.day_pnl_pct:.2f}% >= {settings.daily_profit_stop_pct:.2f}%"
                ),
                severity="BLOCK",
            )

        if state.day_pnl_pct <= settings.daily_loss_stop_pct:
            return RiskDecision(
                allow=False,
                reason=(
                    "Daily loss stop reached: "
                    f"{state.day_pnl_pct:.2f}% <= {settings.daily_loss_stop_pct:.2f}%"
                ),
                severity="BLOCK",
            )

        return RiskDecision(allow=True, reason="Risk checks passed", severity="INFO")
