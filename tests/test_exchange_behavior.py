from __future__ import annotations

import logging
from decimal import Decimal
from urllib import error

import pytest

from src.config.settings import Settings
from src.exchange.base import OrderRequest
from src.exchange.binance_testnet import BinanceFuturesTestnetClient


def test_signed_endpoints_return_empty_in_dry_run_without_keys(
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = Settings(dry_run=True, binance_api_key=None, binance_secret_key=None)
    with caplog.at_level(logging.WARNING):
        client = BinanceFuturesTestnetClient(
            settings=settings, logger=logging.getLogger()
        )

    assert "Missing Binance API credentials" in caplog.text
    assert client.get_balances() == []
    assert client.get_positions() == []


def test_init_raises_without_keys_when_not_dry_run() -> None:
    settings = Settings(dry_run=False, binance_api_key=None, binance_secret_key=None)

    with pytest.raises(RuntimeError, match="BINANCE_API_KEY and BINANCE_SECRET_KEY"):
        BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())


def test_get_mark_price_uses_request_response(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(dry_run=True)
    client = BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())

    def fake_request(method: str, path: str, params=None, signed: bool = False):
        assert method == "GET"
        assert path == "/fapi/v1/premiumIndex"
        assert params == {"symbol": "BTCUSDT"}
        assert signed is False
        return {"symbol": "BTCUSDT", "markPrice": "12345.67"}

    monkeypatch.setattr(client, "_request", fake_request)

    quote = client.get_mark_price("BTCUSDT")

    assert quote.symbol == "BTCUSDT"
    assert str(quote.mark_price) == "12345.67"


def test_get_candles_retries_and_succeeds_on_third_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(dry_run=True, retry_attempts=3)
    client = BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())
    attempts = {"count": 0}

    def flaky_request(method: str, path: str, params=None, signed: bool = False):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise error.URLError("temporary network")
        return [
            [
                1704067200000,
                "100",
                "101",
                "99",
                "100",
                "1",
                1704067260000,
            ]
        ]

    monkeypatch.setattr(client, "_request", flaky_request)

    candles = client.get_candles("BTCUSDT", "1h", limit=1)

    assert len(candles) == 1
    assert attempts["count"] == 3


def test_place_order_raises_when_not_dry_run() -> None:
    settings = Settings(
        dry_run=False,
        binance_api_key="key",
        binance_secret_key="secret",
    )
    client = BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())

    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.1"),
    )

    with pytest.raises(
        NotImplementedError,
        match="Live trading not enabled in Milestone C3",
    ):
        client.place_order(order)
