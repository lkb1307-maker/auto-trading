from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--report_dir", required=True)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def _strategy_diff(path: str) -> str:
    proc = subprocess.run(
        ["git", "diff", "--", path],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() or "(no local diff found for strategy file)"


def main() -> None:
    args = _parse_args()
    report_dir = Path(args.report_dir)
    metrics = json.loads((report_dir / "metrics.json").read_text(encoding="utf-8"))

    gate_summary_path = report_dir / "gate_summary.json"
    gate_summary = (
        json.loads(gate_summary_path.read_text(encoding="utf-8"))
        if gate_summary_path.exists()
        else {"pass": "unknown", "reasons": ["gate_summary.json not found"]}
    )

    content = f"""# Experiment PR Bundle

## Strategy changes
```diff
{_strategy_diff(args.strategy)}
```

## Key metrics
- trades: {metrics['trades']}
- daily_loss_pct: {metrics['daily_loss_pct']}
- daily_profit_pct: {metrics['daily_profit_pct']}
- max_drawdown_pct: {metrics['max_drawdown_pct']}
- sharpe_ratio: {metrics['sharpe_ratio']}

## Gate result
- pass: {gate_summary['pass']}
- reasons: {', '.join(gate_summary.get('reasons', [])) or 'none'}

## Reproduce
```bash
python -m tools.run_experiment --strategy {args.strategy} --out {args.report_dir}
python -m tools.summarize_results --in {args.report_dir} \
  --gates strategy/gates.yaml --json
python -m tools.make_pr_bundle --strategy {args.strategy} \
  --report_dir {args.report_dir} --out {args.out}
```
"""

    Path(args.out).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
