from __future__ import annotations

import time

from src.app.state import BotState
from src.config.settings import Settings
from src.exchange.base import Candle, ExchangeClient
from src.execution.order_router import OrderRouter
from src.risk.risk_manager import RiskManager
from src.strategy.base import Strategy


def run_e2e(
    settings: Settings,
    exchange: ExchangeClient,
    strategy: Strategy,
    risk_manager: RiskManager,
    router: OrderRouter,
) -> dict[str, object]:
    if not settings.dry_run:
        raise RuntimeError("E2E mode requires DRY_RUN=1")

    started_at = time.perf_counter()
    state = BotState()
    state.mark_tick()

    if settings.e2e_real_testnet:
        candles = exchange.get_candles(settings.symbol, settings.timeframe, limit=50)
    else:
        candles = _get_candles_dry_run(exchange=exchange, settings=settings)

    position = state.positions.get(settings.symbol)

    decision = strategy.generate(candles, position=position)
    risk = risk_manager.evaluate(
        settings=settings,
        state=state,
        position=position,
        signal_decision=decision,
    )
    result = router.route(
        signal_decision=decision,
        risk_decision=risk,
        position=position,
        state=state,
        settings=settings,
    )

    return {
        "mode": "e2e",
        "symbol": settings.symbol,
        "timeframe": settings.timeframe,
        "signal": decision.signal,
        "risk_allowed": risk.allow,
        "orders_count": len(result.orders),
        "trades_today": state.trades_today,
        "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
    }


def _get_candles_dry_run(exchange: ExchangeClient, settings: Settings) -> list[Candle]:
    return exchange.get_candles(settings.symbol, settings.timeframe, limit=50)
