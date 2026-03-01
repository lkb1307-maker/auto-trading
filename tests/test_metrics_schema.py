from __future__ import annotations

from tools.metrics_schema import REQUIRED_METRICS_FIELDS


def test_metrics_schema_has_required_fields() -> None:
    metrics = {
        "strategy": "strategy/meanrev_v1.yaml",
        "start": "2024-01-01",
        "end": "2024-01-31",
        "seed": 123,
        "trades": 1,
        "daily_loss_pct": 0.0,
        "daily_profit_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "sharpe_ratio": 0.0,
        "signal": "HOLD",
        "risk_allowed": True,
    }

    missing = REQUIRED_METRICS_FIELDS.difference(metrics)
    assert not missing
