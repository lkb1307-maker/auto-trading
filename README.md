# Binance Futures Auto-Trader (Milestone E)

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


## Milestone D: E2E dry-run mode
- Adds a one-shot end-to-end pipeline runner (`run_e2e`) for safe integration checks.
- Runs one full pass: candles fetch -> strategy decision -> risk evaluation -> order routing.
- Returns a compact summary with signal/risk/order count/trade count fields for quick verification.

**Safety:** E2E mode requires `DRY_RUN=1` and never places real orders.


## Milestone E: Operational hardening
- Exchange adapter now supports configurable request timeout (`HTTP_TIMEOUT_SECONDS`, default 5s).
- `get_candles` and `get_positions` now include bounded retry handling (`RETRY_ATTEMPTS`, default 3) for network failures.
- API key behavior is validated at client initialization:
  - `DRY_RUN=1`: empty keys are allowed with warning logs.
  - `DRY_RUN=0`: keys are required and startup fails fast.
- E2E mode supports optional real Testnet candle fetch via `E2E_REAL_TESTNET=1` while still enforcing `DRY_RUN=1`.
- Structured logs now include `mode`, `symbol`, `timeframe`, `signal`, `risk_allowed`, `orders_count`, and `latency_ms`.

## Experiment pipeline (run-once)
- Entrypoint must use module mode: `python -m src.main`.
- New one-shot mode:

```bash
python -m src.main run-once --strategy strategy/meanrev_v1.yaml --out reports/exp_demo --start 2024-01-01 --end 2024-01-31 --seed 123
```

- Wrapper pipeline examples:

```bash
python -m tools.run_experiment --strategy strategy/meanrev_v1.yaml --out reports/exp_demo --start 2024-01-01 --end 2024-01-31 --seed 123
python -m tools.summarize_results --in reports/exp_demo --gates strategy/gates.yaml --json
python -m tools.make_pr_bundle --strategy strategy/meanrev_v1.yaml --report_dir reports/exp_demo --out reports/exp_demo/pr.md
```

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

# Milestone E additions
HTTP_TIMEOUT_SECONDS=5
RETRY_ATTEMPTS=3
E2E_REAL_TESTNET=0

# Optional notifications
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
NOTIFY_ON_START=0
```

## Run

```bash
python -m src.main --mode e2e
```

## Test

```bash
ruff check .
black --check .
pytest
```
