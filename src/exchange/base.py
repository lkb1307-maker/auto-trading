from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Candle:
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal


@dataclass(frozen=True, slots=True)
class Balance:
    asset: str
    wallet_balance: Decimal
    available_balance: Decimal


@dataclass(frozen=True, slots=True)
class PositionSummary:
    symbol: str
    position_amt: Decimal
    entry_price: Decimal
    unrealized_pnl: Decimal
    leverage: int


@dataclass(frozen=True, slots=True)
class PriceQuote:
    symbol: str
    mark_price: Decimal
    event_time: datetime


@dataclass(frozen=True, slots=True)
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class OrderResult:
    status: str
    symbol: str
    order_id: str
    client_order_id: str | None = None


class ExchangeClient(Protocol):
    def get_mark_price(self, symbol: str) -> PriceQuote: ...

    def get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]: ...

    def get_balances(self) -> list[Balance]: ...

    def get_positions(self, symbol: str | None = None) -> list[PositionSummary]: ...

    def place_order(self, order: OrderRequest) -> OrderResult: ...
