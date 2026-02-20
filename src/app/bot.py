from __future__ import annotations

import logging

from src.app.state import BotState
from src.config.settings import Settings
from src.exchange.base import ExchangeClient


class Bot:
    """Application orchestration shell for Milestone B."""

    def __init__(
        self,
        settings: Settings,
        notifier: object,
        exchange_client: ExchangeClient,
        logger: logging.Logger,
    ) -> None:
        self.settings = settings
        self.notifier = notifier
        self.exchange_client = exchange_client
        self.logger = logger
        self.state = BotState()

    def run_once(self) -> None:
        self.state.mark_tick()
        self.logger.info("bot tick", extra={"tick_count": self.state.tick_count})

        quote = self.exchange_client.get_mark_price(self.settings.symbol)
        candles = self.exchange_client.get_candles(self.settings.symbol, "1m", 10)

        self.logger.info(
            "market snapshot",
            extra={
                "symbol": quote.symbol,
                "mark_price": str(quote.mark_price),
                "candles": len(candles),
                "last_close": str(candles[-1].close_price) if candles else "n/a",
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
