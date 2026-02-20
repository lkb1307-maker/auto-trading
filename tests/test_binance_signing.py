from __future__ import annotations

import logging

from src.config.settings import Settings
from src.exchange.binance_testnet import BinanceFuturesTestnetClient


def test_build_signature_is_deterministic() -> None:
    settings = Settings(
        dry_run=True,
        binance_api_key="test-key",
        binance_secret_key="my-secret",
    )
    client = BinanceFuturesTestnetClient(settings=settings, logger=logging.getLogger())

    payload = "recvWindow=5000&symbol=BTCUSDT&timestamp=1700000000000"

    assert (
        client._build_signature(payload)
        == "5c34482870d881d3f4162b4e1a632b920a0e61156757c19f0487afe9a93d5a64"
    )


def test_encode_params_sorts_keys() -> None:
    encoded = BinanceFuturesTestnetClient._encode_params(
        {"symbol": "BTCUSDT", "timestamp": 2, "recvWindow": 1}
    )

    assert encoded == "recvWindow=1&symbol=BTCUSDT&timestamp=2"
