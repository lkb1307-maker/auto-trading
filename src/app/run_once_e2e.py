from __future__ import annotations

import datetime as dt
import time
from decimal import Decimal

from src.app.state import BotState
from src.config.settings import Settings
from src.exchange.base import Candle, ExchangeClient
from src.execution.order_router import OrderRouter
from src.risk.risk_manager import RiskManager
from src.strategy.base import Strategy

UTC = getattr(dt, "UTC", dt.timezone(dt.timedelta(0)))
CANDLE_LIMIT = 50


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
        candles = exchange.get_candles(
            settings.symbol, settings.timeframe, limit=CANDLE_LIMIT
        )
    else:
        candles = _get_candles_dry_run(settings=settings)

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


def _get_candles_dry_run(settings: Settings) -> list[Candle]:
    start = dt.datetime(2024, 1, 1, tzinfo=UTC)
    return [
        Candle(
            open_time=start + dt.timedelta(minutes=index),
            close_time=start + dt.timedelta(minutes=index + 1),
            open_price=Decimal(100 + index),
            high_price=Decimal(101 + index),
            low_price=Decimal(99 + index),
            close_price=Decimal(100 + index),
            volume=Decimal("1"),
        )
        for index in range(CANDLE_LIMIT)
    ]
