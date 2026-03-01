from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from src.app.run_once_e2e import run_e2e
from src.config.settings import Settings
from src.exchange.binance_testnet import BinanceFuturesTestnetClient
from src.execution.order_router import OrderRouter
from src.risk.risk_manager import RiskManager
from src.strategy.ema_cross import EmaCrossConfig, EmaCrossStrategy


def _read_strategy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("strategy YAML must be an object")
    return data


def _apply_strategy(settings: Settings, strategy_data: dict[str, Any]) -> Settings:
    strategy_block = strategy_data.get("strategy", {})
    risk_block = strategy_data.get("risk", {})

    fast = int(strategy_block.get("fast_period", settings.strategy_fast))
    slow = int(strategy_block.get("slow_period", settings.strategy_slow))
    max_trades = int(risk_block.get("max_trades_per_day", settings.max_trades_per_day))

    if fast >= slow:
        raise ValueError("strategy.fast_period must be less than strategy.slow_period")

    return replace(
        settings,
        symbol=str(strategy_data.get("symbol", settings.symbol)),
        timeframe=str(strategy_data.get("timeframe", settings.timeframe)),
        strategy_fast=fast,
        strategy_slow=slow,
        max_trades_per_day=max_trades,
    )


def run_once(
    args: argparse.Namespace, settings: Settings, logger: Any
) -> dict[str, Any]:
    strategy_path = Path(args.strategy)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    strategy_data = _read_strategy(strategy_path)
    effective_settings = _apply_strategy(settings, strategy_data)

    exchange_client = BinanceFuturesTestnetClient(
        settings=effective_settings, logger=logger
    )
    strategy = EmaCrossStrategy(
        EmaCrossConfig(
            fast_period=effective_settings.strategy_fast,
            slow_period=effective_settings.strategy_slow,
        )
    )
    risk_manager = RiskManager()
    order_router = OrderRouter(exchange_client=exchange_client, logger=logger)

    summary = run_e2e(
        settings=effective_settings,
        exchange=exchange_client,
        strategy=strategy,
        risk_manager=risk_manager,
        router=order_router,
    )

    result = {
        "mode": "run-once",
        "strategy_path": str(strategy_path),
        "seed": args.seed,
        "start": args.start,
        "end": args.end,
        "summary": summary,
    }

    with (out_dir / "run_once_result.json").open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info("run-once completed", extra={"out": str(out_dir), "result": result})
    return result
