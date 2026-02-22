from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from decimal import Decimal

import pytest

from src.app.run_once_e2e import run_e2e
from src.app.types import Signal
from src.config.settings import Settings
from src.exchange.base import (
    Candle,
    OrderRequest,
    OrderResult,
    PositionSummary,
    PriceQuote,
)
from src.execution.order_router import OrderRouter
from src.risk.risk_manager import RiskManager
from src.strategy.base import SignalDecision

UTC = getattr(dt, "UTC", dt.timezone(dt.timedelta(0)))


@dataclass
class FakeExchangeClient:
    mark_price_calls: int = 0
    place_order_calls: int = 0

    def get_mark_price(self, symbol: str) -> PriceQuote:
        self.mark_price_calls += 1
        return PriceQuote(
            symbol=symbol,
            mark_price=Decimal("100"),
            event_time=dt.datetime.now(UTC),
        )

    def get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        _ = (symbol, timeframe, limit)
        return []

    def get_balances(self) -> list[object]:
        return []

    def get_positions(self, symbol: str | None = None) -> list[PositionSummary]:
        _ = symbol
        return []

    def place_order(self, order: OrderRequest) -> OrderResult:
        self.place_order_calls += 1
        return OrderResult(
            status="MOCK_FILLED",
            symbol=order.symbol,
            order_id="dryrun-1",
            client_order_id="DRY_RUN",
        )


class StubStrategy:
    def __init__(self, signal: Signal) -> None:
        self.signal = signal

    def generate(
        self,
        candles: list[Candle],
        position: PositionSummary | None = None,
    ) -> SignalDecision:
        _ = (candles, position)
        return SignalDecision(
            signal=self.signal,
            reason="stub",
            timestamp=dt.datetime.now(UTC),
        )


def _deterministic_candles() -> list[Candle]:
    start = dt.datetime(2024, 1, 1, tzinfo=UTC)
    return [
        Candle(
            open_time=start + dt.timedelta(minutes=i),
            close_time=start + dt.timedelta(minutes=i + 1),
            open_price=Decimal("100"),
            high_price=Decimal("101"),
            low_price=Decimal("99"),
            close_price=Decimal("100"),
            volume=Decimal("1"),
        )
        for i in range(50)
    ]


@pytest.mark.parametrize("signal", [Signal.LONG, Signal.HOLD])
def test_run_e2e_returns_summary_and_updates_trades_conditionally(
    monkeypatch: pytest.MonkeyPatch,
    signal: Signal,
) -> None:
    exchange = FakeExchangeClient()
    captured: dict[str, object] = {}

    def fake_get_candles(symbol: str, timeframe: str, limit: int) -> list[Candle]:
        captured["symbol"] = symbol
        captured["timeframe"] = timeframe
        captured["limit"] = limit
        return _deterministic_candles()

    monkeypatch.setattr(exchange, "get_candles", fake_get_candles)

    summary = run_e2e(
        settings=Settings(dry_run=True),
        exchange=exchange,
        strategy=StubStrategy(signal=signal),
        risk_manager=RiskManager(),
        router=OrderRouter(exchange_client=exchange, logger=logging.getLogger()),
    )

    assert set(summary) == {
        "mode",
        "symbol",
        "timeframe",
        "signal",
        "risk_allowed",
        "orders_count",
        "trades_today",
        "latency_ms",
    }
    assert summary["mode"] == "e2e"
    assert summary["symbol"] == "BTCUSDT"
    assert summary["timeframe"] == "1h"
    assert summary["signal"] in set(Signal)
    assert summary["trades_today"] == summary["orders_count"]
    assert captured == {"symbol": "BTCUSDT", "timeframe": "1h", "limit": 50}


def test_run_e2e_requires_dry_run() -> None:
    exchange = FakeExchangeClient()

    with pytest.raises(RuntimeError, match="E2E mode requires DRY_RUN=1"):
        run_e2e(
            settings=Settings(
                dry_run=False, binance_api_key="key", binance_secret_key="secret"
            ),
            exchange=exchange,
            strategy=StubStrategy(signal=Signal.LONG),
            risk_manager=RiskManager(),
            router=OrderRouter(exchange_client=exchange, logger=logging.getLogger()),
        )
