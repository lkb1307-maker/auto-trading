from __future__ import annotations

import logging

from src.app.state import BotState
from src.config.settings import Settings
from src.exchange.base import ExchangeClient
from src.risk.risk_manager import RiskManager
from src.strategy.base import Strategy


class Bot:
    """Application orchestration shell for Milestone C2."""

    def __init__(
        self,
        settings: Settings,
        notifier: object,
        exchange_client: ExchangeClient,
        strategy: Strategy,
        logger: logging.Logger,
        risk_manager: RiskManager,
    ) -> None:
        self.settings = settings
        self.notifier = notifier
        self.exchange_client = exchange_client
        self.strategy = strategy
        self.logger = logger
        self.risk_manager = risk_manager
        self.state = BotState()

    def run_once(self) -> None:
        self.state.mark_tick()
        self.logger.info("bot tick", extra={"tick_count": self.state.tick_count})

        quote = self.exchange_client.get_mark_price(self.settings.symbol)
        candles = self.exchange_client.get_candles(
            self.settings.symbol,
            self.settings.timeframe,
            limit=self.settings.strategy_slow + 10,
        )
        decision = self.strategy.generate(candles, position=None)
        position = self.state.positions.get(self.settings.symbol)
        risk_decision = self.risk_manager.evaluate(
            settings=self.settings,
            state=self.state,
            position=position,
            signal_decision=decision,
        )

        self.logger.info(
            "market snapshot",
            extra={
                "symbol": quote.symbol,
                "mark_price": str(quote.mark_price),
                "candles": len(candles),
                "last_close": str(candles[-1].close_price) if candles else "n/a",
                "decision_signal": decision.signal,
                "decision_reason": decision.reason,
                "risk_allow": risk_decision.allow,
                "risk_reason": risk_decision.reason,
                "risk_severity": risk_decision.severity,
            },
        )

        if self.settings.dry_run and self.settings.notify_on_start:
            self._send_notification("[DRY_RUN] Auto-trader bot tick")

    def run_loop_placeholder(self, iterations: int = 1) -> None:
        """Safe loop placeholder, bounded by iteration count."""
        for _ in range(iterations):
            self.run_once()

    def _send_notification(self, message: str) -> None:
        send_message = getattr(self.notifier, "send_message", None)
        if callable(send_message):
            send_message(message)
            return

        self.logger.debug("Notifier has no send_message; skipping notification")
