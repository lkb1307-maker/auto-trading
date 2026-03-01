from __future__ import annotations

import argparse
import sys

from src.app.bot import Bot
from src.app.run_once_e2e import run_e2e
from src.app.run_once_experiment import run_once
from src.config.logging_setup import configure_logging
from src.config.settings import load_settings
from src.exchange.binance_testnet import BinanceFuturesTestnetClient
from src.execution.order_router import OrderRouter
from src.notify.telegram import TelegramNotifier
from src.risk.risk_manager import RiskManager
from src.strategy.ema_cross import EmaCrossConfig, EmaCrossStrategy


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["normal", "e2e"], default="normal")

    subparsers = parser.add_subparsers(dest="command")
    run_once_parser = subparsers.add_parser("run-once")
    run_once_parser.add_argument("--strategy", required=True)
    run_once_parser.add_argument("--out", required=True)
    run_once_parser.add_argument("--start")
    run_once_parser.add_argument("--end")
    run_once_parser.add_argument("--seed", type=int, default=123)

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    settings = load_settings()
    logger = configure_logging(settings.log_level)

    if args.command == "run-once":
        try:
            run_once(args=args, settings=settings, logger=logger)
        except Exception:
            logger.exception("run-once failed")
            sys.exit(1)
        return

    notifier = TelegramNotifier(
        token=settings.telegram_token,
        chat_id=settings.telegram_chat_id,
        logger=logger,
    )
    exchange_client = BinanceFuturesTestnetClient(settings=settings, logger=logger)
    strategy = EmaCrossStrategy(
        EmaCrossConfig(
            fast_period=settings.strategy_fast,
            slow_period=settings.strategy_slow,
        )
    )
    risk_manager = RiskManager()
    order_router = OrderRouter(exchange_client=exchange_client, logger=logger)

    if args.mode == "e2e":
        summary = run_e2e(
            settings=settings,
            exchange=exchange_client,
            strategy=strategy,
            risk_manager=risk_manager,
            router=order_router,
        )
        logger.info("e2e dry-run summary", extra={"summary": summary})
        return

    bot = Bot(
        settings=settings,
        notifier=notifier,
        exchange_client=exchange_client,
        strategy=strategy,
        logger=logger,
        risk_manager=risk_manager,
        order_router=order_router,
    )
    bot.run_once()


if __name__ == "__main__":
    main()
