from __future__ import annotations

import pytest

from src.config.settings import SettingsError, load_settings


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "DRY_RUN",
        "BINANCE_API_KEY",
        "BINANCE_SECRET_KEY",
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
        "NOTIFY_ON_START",
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
