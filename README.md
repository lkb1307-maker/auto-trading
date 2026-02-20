# Binance Futures Auto-Trader (Milestone C2)

## Purpose
Milestone C2 introduces a pure **risk layer** on top of the strategy flow with strict
safety defaults:
- public market-data reads,
- strategy signal generation (EMA crossover),
- deterministic risk approval/blocking,
- no live order execution logic.

## Implemented in Milestones C1 + C2
- `ExchangeClient` abstraction and typed domain models (`Candle`, `Balance`, `PositionSummary`, `PriceQuote`, `OrderRequest`, `OrderResult`).
- `BinanceFuturesTestnetClient` using `urllib` + HMAC SHA256 signing for signed calls.
- Structured exchange exceptions:
  - `ExchangeError`
  - `ExchangeAuthError`
  - `ExchangeRateLimitError`
- `Strategy` interface with typed `SignalDecision` output.
- Pure `EmaCrossStrategy` (no network/order side effects) using candle closes only.
- Pure `RiskManager` that evaluates each `SignalDecision` using bot state + settings.
- Bot wiring that fetches candles, generates a strategy decision, evaluates risk, and logs signal + risk outcome each tick.
- No infinite loops and no real order placement in C2.

## Milestone C2 risk rules
- `MAX_TRADES_PER_DAY` (default `20`): block when `state.trades_today >= max`.
- `DAILY_PROFIT_STOP_PCT` (default `5.0`): block when `state.day_pnl_pct >= stop`.
- `DAILY_LOSS_STOP_PCT` (default `-3.0`): block when `state.day_pnl_pct <= stop`.
- `HOLD` signal: returns an `INFO` risk decision and does not allow execution.

## DRY_RUN behavior
- `DRY_RUN=1` (default):
  - Public endpoints work without Binance keys.
  - Signed endpoints (`balances`, `positions`) safely return empty lists when keys are missing.
  - `place_order` returns a mock result and never places real orders.
- `DRY_RUN=0`:
  - `BINANCE_API_KEY` and `BINANCE_SECRET_KEY` are required for signed endpoints.
  - Real order placement is still intentionally disabled in this milestone.

## Environment variables

```env
DRY_RUN=1
LOG_LEVEL=INFO

# Optional for public endpoints; required for signed endpoints when DRY_RUN=0
BINANCE_API_KEY=
BINANCE_SECRET_KEY=

BINANCE_BASE_URL=https://testnet.binancefuture.com
BINANCE_RECV_WINDOW=5000
SYMBOL=BTCUSDT
TIMEFRAME=1h
STRATEGY_FAST=9
STRATEGY_SLOW=21

# Milestone C2 additions
MAX_TRADES_PER_DAY=20
DAILY_PROFIT_STOP_PCT=5.0
DAILY_LOSS_STOP_PCT=-3.0

# Optional notifications
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
NOTIFY_ON_START=0
```

## Run

```bash
python -m src.main
```

## Test

```bash
ruff check .
black --check .
pytest
```

## Next step
- C3 can add execution mocks that only run after a risk `allow=True` decision.
