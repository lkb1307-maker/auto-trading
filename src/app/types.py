from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone


class Signal(enum.StrEnum):
    """High-level trade signals used by future strategy modules."""

    BUY = "buy"
    SELL = "sell"
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
    as_of: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),  # noqa: UP017
    )
