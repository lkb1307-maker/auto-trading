from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", required=True)
    parser.add_argument("--gates", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--md", action="store_true")
    return parser.parse_args()


def evaluate_gates(metrics: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []

    if metrics["trades"] > gates["max_daily_trades"]:
        reasons.append("max_daily_trades exceeded")
    if metrics["daily_loss_pct"] < -float(gates["max_daily_loss_pct"]):
        reasons.append("max_daily_loss_pct exceeded")
    if metrics["daily_profit_pct"] < gates["target_daily_profit_pct"]:
        reasons.append("target_daily_profit_pct not reached")
    if metrics["max_drawdown_pct"] > gates["max_drawdown_pct"]:
        reasons.append("max_drawdown_pct exceeded")
    if metrics["sharpe_ratio"] < gates["min_sharpe"]:
        reasons.append("min_sharpe not reached")
    if metrics["trades"] < gates["min_trades"]:
        reasons.append("min_trades not reached")

    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "key_metrics": {
            "trades": metrics["trades"],
            "daily_loss_pct": metrics["daily_loss_pct"],
            "daily_profit_pct": metrics["daily_profit_pct"],
            "max_drawdown_pct": metrics["max_drawdown_pct"],
            "sharpe_ratio": metrics["sharpe_ratio"],
        },
    }


def main() -> None:
    args = _parse_args()
    in_dir = Path(args.in_dir)
    metrics = json.loads((in_dir / "metrics.json").read_text(encoding="utf-8"))
    gates = json.loads(Path(args.gates).read_text(encoding="utf-8"))

    result = evaluate_gates(metrics=metrics, gates=gates)

    if args.md:
        lines = [
            "# Gate Summary",
            "",
            f"- pass: `{result['pass']}`",
            "- reasons:",
        ]
        if result["reasons"]:
            lines.extend([f"  - {reason}" for reason in result["reasons"]])
        else:
            lines.append("  - none")
        output = "\n".join(lines)
    else:
        output = json.dumps(result, indent=2)

    print(output)


if __name__ == "__main__":
    main()
