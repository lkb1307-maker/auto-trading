from __future__ import annotations

import pytest

from src.config.settings import (
    DEFAULT_BINANCE_BASE_URL,
    DEFAULT_SYMBOL,
    DEFAULT_TIMEFRAME,
    SettingsError,
    load_settings,
)


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "DRY_RUN",
        "BINANCE_API_KEY",
        "BINANCE_SECRET_KEY",
        "BINANCE_BASE_URL",
        "BINANCE_RECV_WINDOW",
        "SYMBOL",
        "TIMEFRAME",
        "STRATEGY_FAST",
        "STRATEGY_SLOW",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
        "NOTIFY_ON_START",
        "MAX_TRADES_PER_DAY",
        "DAILY_PROFIT_STOP_PCT",
        "DAILY_LOSS_STOP_PCT",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_load_settings_allows_missing_binance_keys_in_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DRY_RUN", "1")

    settings = load_settings()

    assert settings.dry_run is True
    assert settings.binance_api_key is None
    assert settings.binance_secret_key is None
    assert settings.binance_base_url == DEFAULT_BINANCE_BASE_URL
    assert settings.binance_recv_window == 5000
    assert settings.symbol == DEFAULT_SYMBOL
    assert settings.timeframe == DEFAULT_TIMEFRAME
    assert settings.strategy_fast == 9
    assert settings.strategy_slow == 21
    assert settings.max_trades_per_day == 20
    assert settings.daily_profit_stop_pct == 5.0
    assert settings.daily_loss_stop_pct == -3.0


def test_load_settings_requires_binance_keys_when_not_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DRY_RUN", "0")

    with pytest.raises(SettingsError):
        load_settings()


def test_load_settings_accepts_binance_keys_when_not_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("BINANCE_API_KEY", "key")
    monkeypatch.setenv("BINANCE_SECRET_KEY", "secret")

    settings = load_settings()

    assert settings.dry_run is False
    assert settings.binance_api_key == "key"
    assert settings.binance_secret_key == "secret"


def test_load_settings_validates_recv_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BINANCE_RECV_WINDOW", "0")

    with pytest.raises(SettingsError):
        load_settings()


def test_load_settings_validates_strategy_periods(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STRATEGY_FAST", "21")
    monkeypatch.setenv("STRATEGY_SLOW", "9")

    with pytest.raises(SettingsError):
        load_settings()


def test_load_settings_validates_daily_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAILY_LOSS_STOP_PCT", "6")
    monkeypatch.setenv("DAILY_PROFIT_STOP_PCT", "5")

    with pytest.raises(SettingsError):
        load_settings()


def test_load_settings_validates_daily_profit_stop_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DAILY_PROFIT_STOP_PCT", "abc")

    with pytest.raises(SettingsError):
        load_settings()
