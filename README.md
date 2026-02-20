# Binance Futures Auto-Trader (Milestone B)

## Purpose
Milestone B introduces a Binance USDT-M Futures **testnet adapter** with strict safety defaults:
- public market-data reads,
- signed account reads with DRY_RUN-safe fallback,
- mock order path in DRY_RUN only,
- no live order execution logic.

## Implemented in Milestone B
- `ExchangeClient` abstraction and typed domain models (`Candle`, `Balance`, `PositionSummary`, `PriceQuote`, `OrderRequest`, `OrderResult`).
- `BinanceFuturesTestnetClient` using `urllib` + HMAC SHA256 signing for signed calls.
- Structured exchange exceptions:
  - `ExchangeError`
  - `ExchangeAuthError`
  - `ExchangeRateLimitError`
- Bot wiring to fetch and log mark price + recent candles each tick.
- No infinite loops and no real order placement.

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
- Milestone C can add strategy logic on top of the current exchange abstraction.
