from __future__ import annotations

from src.app.state import BotState
from src.config.settings import Settings
from src.exchange.base import ExchangeClient
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

    state = BotState()
    state.mark_tick()

    candles = exchange.get_candles(settings.symbol, settings.timeframe, limit=50)
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
        "signal": decision.signal,
        "risk_allowed": risk.allow,
        "orders_count": len(result.orders),
        "trades_today": state.trades_today,
    }
