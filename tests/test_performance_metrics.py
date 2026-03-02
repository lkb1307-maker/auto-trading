from __future__ import annotations

from src.performance.metrics import summarize


def test_summarize_empty_trades() -> None:
    summary = summarize([])

    assert summary["total_trades"] == 0
    assert summary["win_rate"] == 0.0
    assert summary["simple_mdd_usdt"] == 0.0


def test_summarize_all_wins() -> None:
    summary = summarize(
        [
            {"pnl_usdt": 1.0},
            {"pnl_usdt": 2.0},
            {"pnl_usdt": 3.0},
        ]
    )

    assert summary["total_trades"] == 3
    assert summary["win_rate"] == 100.0
    assert summary["avg_loss_usdt"] == 0.0


def test_summarize_mixed_and_consecutive_losses_and_mdd() -> None:
    summary = summarize(
        [
            {"pnl_usdt": 5.0},
            {"pnl_usdt": -2.0},
            {"pnl_usdt": -3.0},
            {"pnl_usdt": 1.0},
            {"pnl_usdt": -4.0},
        ]
    )

    assert summary["total_trades"] == 5
    assert summary["win_rate"] == 40.0
    assert summary["max_consecutive_losses"] == 2
    assert summary["simple_mdd_usdt"] == 8.0
