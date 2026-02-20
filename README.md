# Binance Futures Auto-Trader (Milestone C1)

## Purpose
Milestone C1 introduces a pure **strategy layer** on top of the Binance USDT-M Futures
testnet adapter with strict safety defaults:
- public market-data reads,
- signed account reads with DRY_RUN-safe fallback,
- strategy-only signal generation (EMA crossover),
- no live order execution logic.

## Implemented in Milestone C1
- `ExchangeClient` abstraction and typed domain models (`Candle`, `Balance`, `PositionSummary`, `PriceQuote`, `OrderRequest`, `OrderResult`).
- `BinanceFuturesTestnetClient` using `urllib` + HMAC SHA256 signing for signed calls.
- Structured exchange exceptions:
  - `ExchangeError`
  - `ExchangeAuthError`
  - `ExchangeRateLimitError`
- `Strategy` interface with typed `SignalDecision` output.
- Pure `EmaCrossStrategy` (no network/order side effects) using candle closes only.
- Bot wiring to fetch candles, generate a strategy decision, and log signal + reason each tick.
- No infinite loops and no real order placement in C1.

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

# Milestone B additions
BINANCE_BASE_URL=https://testnet.binancefuture.com
BINANCE_RECV_WINDOW=5000
SYMBOL=BTCUSDT
TIMEFRAME=1h
STRATEGY_FAST=9
STRATEGY_SLOW=21

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

## Notes
- This repository intentionally avoids external dependencies for the exchange adapter.
- C1 strategy output is signal-only (`LONG`, `SHORT`, `HOLD`) and does not place orders.
- A future milestone can map strategy signals to risk-managed order execution.
