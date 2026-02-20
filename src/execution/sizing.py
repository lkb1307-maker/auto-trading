from __future__ import annotations

from src.config.settings import Settings


def calculate_order_qty(settings: Settings, price: float) -> float:
    if price <= 0:
        raise ValueError("price must be greater than zero")
    return settings.order_notional_usdt / price
