from __future__ import annotations

import importlib
import importlib.util
import os
from dataclasses import dataclass

from .constants import DEFAULT_LOG_LEVEL

DEFAULT_BINANCE_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_MAX_TRADES_PER_DAY = 20
DEFAULT_DAILY_PROFIT_STOP_PCT = 5.0
DEFAULT_DAILY_LOSS_STOP_PCT = -3.0


@dataclass(frozen=True, slots=True)
class Settings:
    dry_run: bool = True
    binance_api_key: str | None = None
    binance_secret_key: str | None = None
    binance_base_url: str = DEFAULT_BINANCE_BASE_URL
    binance_recv_window: int = 5000
    symbol: str = DEFAULT_SYMBOL
    timeframe: str = DEFAULT_TIMEFRAME
    strategy_fast: int = 9
    strategy_slow: int = 21
    max_trades_per_day: int = DEFAULT_MAX_TRADES_PER_DAY
    daily_profit_stop_pct: float = DEFAULT_DAILY_PROFIT_STOP_PCT
    daily_loss_stop_pct: float = DEFAULT_DAILY_LOSS_STOP_PCT
    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    notify_on_start: bool = False
    log_level: str = DEFAULT_LOG_LEVEL


class SettingsError(ValueError):
    """Raised when environment configuration is invalid."""


def _load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return

    dotenv_module = importlib.import_module("dotenv")
    load_dotenv = getattr(dotenv_module, "load_dotenv", None)
    if callable(load_dotenv):
        load_dotenv(override=False)


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer") from exc

    if value <= 0:
        raise SettingsError(f"{name} must be greater than zero")

    return value


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        return float(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be a float") from exc


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise SettingsError(
            f"Missing required environment variable: {name}. "
            "Set it in your shell or .env file."
        )
    return value.strip()


def load_settings() -> Settings:
    _load_dotenv_if_available()

    dry_run = _get_bool("DRY_RUN", default=True)

    binance_api_key = os.getenv("BINANCE_API_KEY")
    binance_secret_key = os.getenv("BINANCE_SECRET_KEY")

    if not dry_run:
        binance_api_key = _require("BINANCE_API_KEY")
        binance_secret_key = _require("BINANCE_SECRET_KEY")

    strategy_fast = _get_int("STRATEGY_FAST", default=9)
    strategy_slow = _get_int("STRATEGY_SLOW", default=21)

    if strategy_fast >= strategy_slow:
        raise SettingsError("STRATEGY_FAST must be less than STRATEGY_SLOW")

    max_trades_per_day = _get_int("MAX_TRADES_PER_DAY", DEFAULT_MAX_TRADES_PER_DAY)
    daily_profit_stop_pct = _get_float(
        "DAILY_PROFIT_STOP_PCT",
        DEFAULT_DAILY_PROFIT_STOP_PCT,
    )
    daily_loss_stop_pct = _get_float(
        "DAILY_LOSS_STOP_PCT",
        DEFAULT_DAILY_LOSS_STOP_PCT,
    )

    if daily_loss_stop_pct >= daily_profit_stop_pct:
        raise SettingsError(
            "DAILY_LOSS_STOP_PCT must be less than DAILY_PROFIT_STOP_PCT"
        )

    return Settings(
        dry_run=dry_run,
        binance_api_key=binance_api_key,
        binance_secret_key=binance_secret_key,
        binance_base_url=os.getenv("BINANCE_BASE_URL", DEFAULT_BINANCE_BASE_URL),
        binance_recv_window=_get_int("BINANCE_RECV_WINDOW", default=5000),
        symbol=os.getenv("SYMBOL", DEFAULT_SYMBOL),
        timeframe=os.getenv("TIMEFRAME", DEFAULT_TIMEFRAME),
        strategy_fast=strategy_fast,
        strategy_slow=strategy_slow,
        max_trades_per_day=max_trades_per_day,
        daily_profit_stop_pct=daily_profit_stop_pct,
        daily_loss_stop_pct=daily_loss_stop_pct,
        telegram_token=os.getenv("TELEGRAM_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        notify_on_start=_get_bool("NOTIFY_ON_START", default=False),
        log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
    )
