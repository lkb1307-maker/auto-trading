from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.app.state import BotState
from src.app.types import PositionSummary, Signal
from src.config.settings import Settings
from src.exchange.base import ExchangeClient, OrderRequest, OrderResult
from src.execution.sizing import calculate_order_qty
from src.risk.risk_manager import RiskDecision
from src.strategy.base import SignalDecision

UTC = getattr(datetime, "UTC", timezone(timedelta(0)))


@dataclass(slots=True)
class ExecutionResult:
    orders: list[OrderResult]
    skipped_reason: str | None = None


class OrderRouter:
    """Converts approved decisions into simulated orders."""

    def __init__(self, exchange_client: ExchangeClient, logger: logging.Logger) -> None:
        self.exchange_client = exchange_client
        self.logger = logger

    def route(
        self,
        signal_decision: SignalDecision,
        risk_decision: RiskDecision,
        position: PositionSummary | None,
        state: BotState,
        settings: Settings,
    ) -> ExecutionResult:
        if not risk_decision.allow:
            return ExecutionResult(orders=[], skipped_reason=risk_decision.reason)

        if signal_decision.signal == Signal.HOLD:
            return ExecutionResult(orders=[], skipped_reason="Signal is HOLD")

        if (
            signal_decision.signal == Signal.LONG
            and self._position_side(position) == Signal.LONG
        ):
            return ExecutionResult(orders=[], skipped_reason="Already LONG")

        if (
            signal_decision.signal == Signal.SHORT
            and self._position_side(position) == Signal.SHORT
        ):
            return ExecutionResult(orders=[], skipped_reason="Already SHORT")

        quote = self.exchange_client.get_mark_price(settings.symbol)
        quantity = calculate_order_qty(settings=settings, price=float(quote.mark_price))
        side = "BUY" if signal_decision.signal == Signal.LONG else "SELL"
        order_request = OrderRequest(
            symbol=settings.symbol,
            side=side,
            order_type="MARKET",
            quantity=Decimal(str(quantity)),
        )
        order_result = self.exchange_client.place_order(order_request)
        state.trades_today += 1
        state.last_trade_at = datetime.now(UTC)
        self.logger.info(
            "simulated execution routed",
            extra={
                "symbol": settings.symbol,
                "signal": signal_decision.signal,
                "order_side": side,
                "qty": quantity,
                "order_status": order_result.status,
                "order_id": order_result.order_id,
            },
        )
        return ExecutionResult(orders=[order_result], skipped_reason=None)

    @staticmethod
    def _position_side(position: PositionSummary | None) -> Signal | None:
        if position is None or position.size == 0:
            return None
        return Signal.LONG if position.size > 0 else Signal.SHORT
