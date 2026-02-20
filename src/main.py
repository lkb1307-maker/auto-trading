from __future__ import annotations

from src.app.bot import Bot
from src.config.logging_setup import configure_logging
from src.config.settings import load_settings
from src.exchange.binance_testnet import BinanceFuturesTestnetClient
from src.execution.order_router import OrderRouter
from src.notify.telegram import TelegramNotifier
from src.risk.risk_manager import RiskManager
from src.strategy.ema_cross import EmaCrossConfig, EmaCrossStrategy


def main() -> None:
    settings = load_settings()
    logger = configure_logging(settings.log_level)

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

    bot = Bot(
        settings=settings,
        notifier=notifier,
        exchange_client=exchange_client,
        strategy=strategy,
        logger=logger,
        risk_manager=RiskManager(),
        order_router=OrderRouter(exchange_client=exchange_client, logger=logger),
    )
    bot.run_once()


if __name__ == "__main__":
    main()
