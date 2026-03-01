from __future__ import annotations

from tools.summarize_results import evaluate_gates


def test_evaluate_gates_pass() -> None:
    metrics = {
        "trades": 5,
        "daily_loss_pct": -1.0,
        "daily_profit_pct": 2.0,
        "max_drawdown_pct": 3.0,
        "sharpe_ratio": 1.2,
    }
    gates = {
        "max_daily_trades": 10,
        "max_daily_loss_pct": 3.0,
        "target_daily_profit_pct": 1.0,
        "max_drawdown_pct": 5.0,
        "min_sharpe": 0.8,
        "min_trades": 3,
    }

    result = evaluate_gates(metrics=metrics, gates=gates)

    assert result["pass"] is True
    assert result["reasons"] == []


def test_evaluate_gates_fail_with_reasons() -> None:
    metrics = {
        "trades": 0,
        "daily_loss_pct": -4.0,
        "daily_profit_pct": 0.0,
        "max_drawdown_pct": 7.0,
        "sharpe_ratio": 0.1,
    }
    gates = {
        "max_daily_trades": 10,
        "max_daily_loss_pct": 3.0,
        "target_daily_profit_pct": 1.0,
        "max_drawdown_pct": 5.0,
        "min_sharpe": 0.8,
        "min_trades": 3,
    }

    result = evaluate_gates(metrics=metrics, gates=gates)

    assert result["pass"] is False
    assert len(result["reasons"]) == 5
