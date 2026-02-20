from __future__ import annotations

import logging

import pytest

from src.config.settings import Settings
from src.exchange.binance_testnet import BinanceFuturesTestnetClient, ExchangeAuthError


def test_signed_endpoints_return_empty_in_dry_run_without_keys() -> None:
    settings = Settings(dry_run=True, binance_api_key=None, binance_secret_key=None)
    client = BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())

    assert client.get_balances() == []
    assert client.get_positions() == []


def test_signed_endpoints_raise_without_keys_when_not_dry_run() -> None:
    settings = Settings(dry_run=False, binance_api_key=None, binance_secret_key=None)
    client = BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())

    with pytest.raises(ExchangeAuthError):
        client.get_balances()


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
