from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

import src.app.run_once_e2e as e2e_module
from src.app.types import Signal
from src.config.settings import Settings
from src.exchange.base import Candle, OrderRequest, OrderResult, PriceQuote


def _build_candles(limit: int) -> list[Candle]:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for idx in range(limit):
        close = Decimal("100") if idx < limit - 1 else Decimal("150")
        candles.append(
            Candle(
                open_time=start + timedelta(hours=idx),
                close_time=start + timedelta(hours=idx + 1),
                open_price=close,
                high_price=close,
                low_price=close,
                close_price=close,
                volume=Decimal("10"),
            )
        )
    return candles


def test_run_e2e_executes_pipeline_and_increments_trade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(dry_run=True)
    candles_limit = settings.strategy_slow + 10
    events = {
        "candles_called": False,
        "risk_called": False,
        "place_order_called": False,
    }

    monkeypatch.setattr("src.app.run_once_e2e.load_settings", lambda: settings)
    monkeypatch.setattr(
        "src.app.run_once_e2e.configure_logging",
        lambda _level: logging.getLogger("test-e2e"),
    )

    def fake_get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        assert symbol == settings.symbol
        assert timeframe == settings.timeframe
        assert limit == candles_limit
        events["candles_called"] = True
        return _build_candles(limit)

    def fake_get_mark_price(self, symbol: str) -> PriceQuote:
        return PriceQuote(
            symbol=symbol,
            mark_price=Decimal("100"),
            event_time=datetime.now(UTC),
        )

    def fake_place_order(self, _order: OrderRequest) -> OrderResult:
        events["place_order_called"] = True
        return OrderResult(
            status="MOCK_FILLED",
            symbol=settings.symbol,
            order_id="dryrun-1",
            client_order_id="DRY_RUN",
        )

    original_evaluate = e2e_module.RiskManager.evaluate

    def wrapped_evaluate(self, *args, **kwargs):
        events["risk_called"] = True
        return original_evaluate(self, *args, **kwargs)

    monkeypatch.setattr(
        "src.exchange.binance_testnet.BinanceFuturesTestnetClient.get_candles",
        fake_get_candles,
    )
    monkeypatch.setattr(
        "src.exchange.binance_testnet.BinanceFuturesTestnetClient.get_mark_price",
        fake_get_mark_price,
    )
    monkeypatch.setattr(
        "src.exchange.binance_testnet.BinanceFuturesTestnetClient.place_order",
        fake_place_order,
    )
    monkeypatch.setattr("src.app.run_once_e2e.RiskManager.evaluate", wrapped_evaluate)

    summary = e2e_module.run_e2e()

    assert events["candles_called"] is True
    assert events["risk_called"] is True
    assert events["place_order_called"] is True
    assert summary["signal"] == Signal.LONG
    assert summary["risk_allowed"] is True
    assert summary["orders_count"] == 1
    assert summary["trades_today"] == 1


def test_run_e2e_requires_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.app.run_once_e2e.load_settings", lambda: Settings(dry_run=False)
    )

    with pytest.raises(RuntimeError, match="E2E mode requires DRY_RUN=1"):
        e2e_module.run_e2e()
