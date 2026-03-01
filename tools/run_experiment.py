from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--start")
    parser.add_argument("--end")
    return parser.parse_args()


def _build_metrics(result: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    summary = result["summary"]
    trades = int(summary.get("orders_count", 0))

    return {
        "strategy": args.strategy,
        "start": args.start,
        "end": args.end,
        "seed": args.seed,
        "trades": trades,
        "daily_loss_pct": 0.0,
        "daily_profit_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "sharpe_ratio": 0.0,
        "signal": summary.get("signal"),
        "risk_allowed": bool(summary.get("risk_allowed", False)),
        "orders_count": trades,
        "latency_ms": summary.get("latency_ms"),
    }


def main() -> None:
    args = _parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "src.main",
        "run-once",
        "--strategy",
        args.strategy,
        "--out",
        str(out_dir),
        "--seed",
        str(args.seed),
    ]
    if args.start:
        cmd.extend(["--start", args.start])
    if args.end:
        cmd.extend(["--end", args.end])

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if proc.returncode != 0:
        logs = out_dir / "logs.txt"
        logs.write_text(
            f"$ {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}",
            encoding="utf-8",
        )
        raise SystemExit(proc.returncode)

    run_once_result_path = out_dir / "run_once_result.json"
    result = json.loads(run_once_result_path.read_text(encoding="utf-8"))

    metrics = _build_metrics(result=result, args=args)
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )

    summary_md = "\n".join(
        [
            "# Experiment Summary",
            "",
            f"- strategy: `{metrics['strategy']}`",
            f"- seed: `{metrics['seed']}`",
            f"- period: `{metrics['start']} ~ {metrics['end']}`",
            f"- signal: `{metrics['signal']}`",
            f"- trades: `{metrics['trades']}`",
            f"- sharpe: `{metrics['sharpe_ratio']}`",
        ]
    )
    (out_dir / "summary.md").write_text(summary_md, encoding="utf-8")


if __name__ == "__main__":
    main()
