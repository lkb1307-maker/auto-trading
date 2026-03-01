from __future__ import annotations


def format_report(summary: dict[str, float | int]) -> str:
    return (
        "Performance Report\n"
        f"total_trades: {summary.get('total_trades', 0)}\n"
        f"win_rate: {summary.get('win_rate', 0.0):.2f}%\n"
        f"total_pnl_usdt: {summary.get('total_pnl_usdt', 0.0):.4f}\n"
        f"avg_pnl_usdt: {summary.get('avg_pnl_usdt', 0.0):.4f}\n"
        f"avg_win_usdt: {summary.get('avg_win_usdt', 0.0):.4f}\n"
        f"avg_loss_usdt: {summary.get('avg_loss_usdt', 0.0):.4f}\n"
        f"max_consecutive_losses: {summary.get('max_consecutive_losses', 0)}\n"
        f"simple_mdd_usdt: {summary.get('simple_mdd_usdt', 0.0):.4f}"
    )
