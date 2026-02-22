from __future__ import annotations

from src.app.state import BotState
from src.config.logging_setup import configure_logging
from src.config.settings import load_settings
from src.exchange.binance_testnet import BinanceFuturesTestnetClient
from src.execution.order_router import OrderRouter
from src.risk.risk_manager import RiskManager
from src.strategy.ema_cross import EmaCrossConfig, EmaCrossStrategy


def run_e2e() -> dict[str, object]:
    """Execute one full strategy/risk/execution pipeline in dry-run mode."""
    settings = load_settings()
    if not settings.dry_run:
        raise RuntimeError("E2E mode requires DRY_RUN=1")

    logger = configure_logging(settings.log_level)
    exchange = BinanceFuturesTestnetClient(settings=settings, logger=logger)

    candles = exchange.get_candles(
        settings.symbol,
        settings.timeframe,
        limit=settings.strategy_slow + 10,
    )

    strategy = EmaCrossStrategy(
        EmaCrossConfig(
            fast_period=settings.strategy_fast,
            slow_period=settings.strategy_slow,
        )
    )
    risk_manager = RiskManager()
    router = OrderRouter(exchange_client=exchange, logger=logger)
    state = BotState()

    signal_decision = strategy.generate(candles, position=None)
    risk_decision = risk_manager.evaluate(
        settings=settings,
        state=state,
        position=None,
        signal_decision=signal_decision,
    )
    execution_result = router.route(
        signal_decision=signal_decision,
        risk_decision=risk_decision,
        position=None,
        state=state,
        settings=settings,
    )

    logger.info("SIGNAL=%s", signal_decision.signal)
    logger.info("RISK=%s", risk_decision.allow)
    logger.info("EXECUTED=%s", len(execution_result.orders) > 0)
    logger.info("TRADES_TODAY=%s", state.trades_today)

    return {
        "signal": signal_decision.signal,
        "risk_allowed": risk_decision.allow,
        "orders_count": len(execution_result.orders),
        "trades_today": state.trades_today,
    }
