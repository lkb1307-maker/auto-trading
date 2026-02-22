# Binance Futures Auto-Trader (Milestone C3)

## Purpose
Milestone C3 introduces a simulated **execution layer** that routes strategy + risk decisions
into mock orders with strict safety defaults:
- public market-data reads,
- strategy signal generation (EMA crossover),
- deterministic risk approval/blocking,
- simulated order routing only in DRY_RUN.

## Implemented in Milestones C1 + C2 + C3
- `ExchangeClient` abstraction and typed domain models (`Candle`, `Balance`, `PositionSummary`, `PriceQuote`, `OrderRequest`, `OrderResult`).
- `BinanceFuturesTestnetClient` using `urllib` + HMAC SHA256 signing for signed calls.
- Structured exchange exceptions:
  - `ExchangeError`
  - `ExchangeAuthError`
  - `ExchangeRateLimitError`
- `Strategy` interface with typed `SignalDecision` output.
- Pure `EmaCrossStrategy` (no network/order side effects) using candle closes only.
- Pure `RiskManager` that evaluates each `SignalDecision` using bot state + settings.
- `OrderRouter` execution layer that converts allowed decisions into DRY_RUN mock orders.
- Bot wiring that fetches candles, generates strategy decision, evaluates risk, routes execution, and logs outcomes each tick.
- No infinite loops and no real order placement.

## Milestone C3 execution rules
- If `risk_decision.allow` is `False`, router skips order execution.
- If strategy signal is `HOLD`, router skips order execution.
- If signal is `LONG` and current position is not long, router simulates a long market order.
- If signal is `SHORT` and current position is not short, router simulates a short market order.
- On each simulated order:
  - `state.trades_today` is incremented.
  - `state.last_trade_at` is set to current UTC time.

## DRY_RUN safety guarantees
- `DRY_RUN=1` (default):
  - Public endpoints work without Binance keys.
  - Signed endpoints (`balances`, `positions`) safely return empty lists when keys are missing.
  - `place_order` returns a mock `OrderResult` and never places a real order.
- `DRY_RUN=0`:
  - `BINANCE_API_KEY` and `BINANCE_SECRET_KEY` are required for signed endpoints.
  - `place_order` raises `NotImplementedError("Live trading not enabled in Milestone C3")`.

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

MAX_TRADES_PER_DAY=20
DAILY_PROFIT_STOP_PCT=5.0
DAILY_LOSS_STOP_PCT=-3.0

# Milestone C3 additions
ORDER_NOTIONAL_USDT=50.0
NOTIFY_ON_TRADE=0

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
