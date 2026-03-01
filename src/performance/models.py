from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TradeOpenEvent:
    ts_open: str
    symbol: str
    side: str
    qty: float
    entry_price: float
    reason_open: str | None = None
    strategy_name: str | None = None
    strategy_version: str | None = None
    mode: str | None = None
    exchange_order_ids: str | None = None
    meta_json: str | None = None


@dataclass(frozen=True, slots=True)
class TradeCloseEvent:
    ts_close: str
    exit_price: float | None = None
    fees: float | None = None
    pnl_usdt: float | None = None
    pnl_pct: float | None = None
    reason_close: str | None = None
    exchange_order_ids: str | None = None
    meta_json: str | None = None


@dataclass(frozen=True, slots=True)
class TradeRecord:
    trade_id: str
    ts_open: str
    ts_close: str | None
    symbol: str
    side: str
    qty: float
    entry_price: float
    exit_price: float | None
    fees: float | None
    pnl_usdt: float | None
    pnl_pct: float | None
    reason_open: str | None
    reason_close: str | None
    strategy_name: str | None
    strategy_version: str | None
    mode: str | None
    exchange_order_ids: str | None
    meta_json: str | None
