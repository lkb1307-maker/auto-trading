from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import StrEnum

UTC = getattr(dt, "UTC", dt.timezone(dt.timedelta(0)))


class Signal(StrEnum):
    """High-level trade signals used by future strategy modules."""

    LONG = "long"
    SHORT = "short"
    HOLD = "hold"


@dataclass(slots=True)
class OrderRequest:
    """Intent to place an order. Execution is intentionally not implemented."""

    symbol: str
    side: Signal
    quantity: float
    reduce_only: bool = False


@dataclass(slots=True)
class PositionSummary:
    """Read-model for a position snapshot."""

    symbol: str
    size: float = 0.0
    entry_price: float | None = None
    unrealized_pnl: float = 0.0
    as_of: dt.datetime = field(
        default_factory=lambda: dt.datetime.now(UTC),
    )
