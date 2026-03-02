from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize(trades: Iterable[Any]) -> dict[str, float | int]:
    pnl_values: list[float] = []
    for trade in trades:
        pnl = _safe_float(getattr(trade, "pnl_usdt", None))
        if pnl is None and isinstance(trade, dict):
            pnl = _safe_float(trade.get("pnl_usdt"))
        if pnl is not None:
            pnl_values.append(pnl)

    total_trades = len(pnl_values)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl_usdt": 0.0,
            "avg_pnl_usdt": 0.0,
            "avg_win_usdt": 0.0,
            "avg_loss_usdt": 0.0,
            "max_consecutive_losses": 0,
            "simple_mdd_usdt": 0.0,
        }

    wins = [p for p in pnl_values if p > 0]
    losses = [p for p in pnl_values if p < 0]

    max_consecutive_losses = 0
    streak = 0
    for pnl in pnl_values:
        if pnl < 0:
            streak += 1
            max_consecutive_losses = max(max_consecutive_losses, streak)
        else:
            streak = 0

    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnl_values:
        equity += pnl
        peak = max(peak, equity)
        drawdown = peak - equity
        max_drawdown = max(max_drawdown, drawdown)

    return {
        "total_trades": total_trades,
        "win_rate": (len(wins) / total_trades) * 100.0,
        "total_pnl_usdt": sum(pnl_values),
        "avg_pnl_usdt": sum(pnl_values) / total_trades,
        "avg_win_usdt": (sum(wins) / len(wins)) if wins else 0.0,
        "avg_loss_usdt": (sum(losses) / len(losses)) if losses else 0.0,
        "max_consecutive_losses": max_consecutive_losses,
        "simple_mdd_usdt": max_drawdown,
    }
