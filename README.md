# Binance Futures Auto-Trader (Milestone A Skeleton)

## Purpose
Milestone A establishes a production-minded project skeleton for a Binance futures auto-trader that supports local development and testnet experimentation.

This milestone focuses on:
- typed and testable foundations,
- config loading and validation,
- structured logging,
- dependency-injected bot orchestration,
- CI checks for lint/format/tests.

## Non-goals (Milestone A)
- No real trading logic.
- No live order execution.
- No infinite loop by default.

## Project layout

```text
auto-trader/
  src/
    app/
      bot.py
      state.py
      types.py
    config/
      constants.py
      logging_setup.py
      settings.py
    notify/
      telegram.py
    main.py
  tests/
    test_settings.py
    test_state.py
  logs/
  .github/workflows/ci.yml
  .gitignore
  pyproject.toml
  requirements.txt
  README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (optional):

```env
# Safe skeleton mode (default true)
DRY_RUN=1
NOTIFY_ON_START=0
LOG_LEVEL=INFO

# Required only when DRY_RUN=0
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Optional for Telegram notifications
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### DRY_RUN behavior
- `DRY_RUN=1` (default): Binance API keys are not required.
- `DRY_RUN=0`: `BINANCE_API_KEY` and `BINANCE_SECRET_KEY` are required and validated at startup.

## Run

```bash
python -m src.main
```

## Test

```bash
pytest
```

## Quality checks

```bash
ruff check .
black --check .
```

## Next milestones
- **Milestone B:** Binance client abstraction + testnet market data adapter.
- **Milestone C:** Strategy interface + first signal generator.
- **Milestone D:** Risk management and order execution guards.
- **Milestone E:** Persistence, metrics, and operational tooling.
