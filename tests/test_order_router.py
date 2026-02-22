from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from src.app.state import BotState
from src.app.types import PositionSummary, Signal
from src.config.settings import Settings
from src.exchange.base import OrderRequest, OrderResult, PriceQuote
from src.execution.order_router import OrderRouter
from src.risk.risk_manager import RiskDecision
from src.strategy.base import SignalDecision


@dataclass
class FakeExchangeClient:
    mark_price_calls: int = 0
    place_order_calls: int = 0

    def get_mark_price(self, symbol: str) -> PriceQuote:
        self.mark_price_calls += 1
        return PriceQuote(
            symbol=symbol,
            mark_price=Decimal("100"),
            event_time=datetime.now(timezone.utc),  # noqa: UP017
        )

    def place_order(self, order: OrderRequest) -> OrderResult:
        self.place_order_calls += 1
        return OrderResult(
            status="MOCK_FILLED",
            symbol=order.symbol,
            order_id="dryrun-1",
            client_order_id="DRY_RUN",
        )


def _signal_decision(signal: Signal) -> SignalDecision:
    return SignalDecision(
        signal=signal,
        reason="test",
        timestamp=datetime.now(timezone.utc),  # noqa: UP017
    )


def test_route_skips_when_risk_blocked() -> None:
    exchange = FakeExchangeClient()
    router = OrderRouter(exchange_client=exchange, logger=logging.getLogger())
    state = BotState()

    result = router.route(
        signal_decision=_signal_decision(Signal.LONG),
        risk_decision=RiskDecision(allow=False, reason="blocked", severity="BLOCK"),
        position=None,
        state=state,
        settings=Settings(),
    )

    assert result.orders == []
    assert result.skipped_reason == "blocked"
    assert exchange.mark_price_calls == 0
    assert exchange.place_order_calls == 0


def test_route_skips_when_signal_hold() -> None:
    exchange = FakeExchangeClient()
    router = OrderRouter(exchange_client=exchange, logger=logging.getLogger())

    result = router.route(
        signal_decision=_signal_decision(Signal.HOLD),
        risk_decision=RiskDecision(allow=True, reason="ok", severity="INFO"),
        position=None,
        state=BotState(),
        settings=Settings(),
    )

    assert result.orders == []
    assert result.skipped_reason == "Signal is HOLD"
    assert exchange.mark_price_calls == 0
    assert exchange.place_order_calls == 0


def test_route_long_with_no_position_places_mock_order() -> None:
    exchange = FakeExchangeClient()
    router = OrderRouter(exchange_client=exchange, logger=logging.getLogger())
    state = BotState()

    result = router.route(
        signal_decision=_signal_decision(Signal.LONG),
        risk_decision=RiskDecision(allow=True, reason="ok", severity="INFO"),
        position=None,
        state=state,
        settings=Settings(order_notional_usdt=50.0),
    )

    assert len(result.orders) == 1
    assert exchange.mark_price_calls == 1
    assert exchange.place_order_calls == 1
    assert state.trades_today == 1
    assert state.last_trade_at is not None


def test_route_short_with_opposite_position_places_mock_order() -> None:
    exchange = FakeExchangeClient()
    router = OrderRouter(exchange_client=exchange, logger=logging.getLogger())

    result = router.route(
        signal_decision=_signal_decision(Signal.SHORT),
        risk_decision=RiskDecision(allow=True, reason="ok", severity="INFO"),
        position=PositionSummary(symbol="BTCUSDT", size=1.0),
        state=BotState(),
        settings=Settings(),
    )

    assert len(result.orders) == 1
    assert exchange.mark_price_calls == 1
    assert exchange.place_order_calls == 1


def test_route_skips_when_already_same_side() -> None:
    exchange = FakeExchangeClient()
    router = OrderRouter(exchange_client=exchange, logger=logging.getLogger())

    result = router.route(
        signal_decision=_signal_decision(Signal.SHORT),
        risk_decision=RiskDecision(allow=True, reason="ok", severity="INFO"),
        position=PositionSummary(symbol="BTCUSDT", size=-1.0),
        state=BotState(),
        settings=Settings(),
    )

    assert result.orders == []
    assert result.skipped_reason == "Already SHORT"
    assert exchange.mark_price_calls == 0
    assert exchange.place_order_calls == 0
