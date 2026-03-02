from __future__ import annotations

import sqlite3

from src.performance.models import TradeCloseEvent, TradeOpenEvent
from src.performance.store import PerformanceStore


def test_init_db_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "perf.sqlite3"
    store = PerformanceStore(db_path)

    store.init_db()

    with sqlite3.connect(db_path) as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trades'"
        ).fetchone()
        assert table == ("trades",)

        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='trades'"
            ).fetchall()
        }
        assert "idx_trades_ts_open" in indexes
        assert "idx_trades_ts_close" in indexes
        assert "idx_trades_strategy_name" in indexes


def test_record_open_inserts_row(tmp_path) -> None:
    db_path = tmp_path / "perf.sqlite3"
    store = PerformanceStore(db_path)
    store.init_db()

    trade_id = store.record_open(
        TradeOpenEvent(
            ts_open="2025-01-01T00:00:00+00:00",
            symbol="BTCUSDT",
            side="BUY",
            qty=0.01,
            entry_price=100.0,
            reason_open="ema_cross",
            strategy_name="ema",
            strategy_version="v1",
            mode="paper",
        )
    )

    trades = store.get_trades()
    assert len(trades) == 1
    assert trades[0].trade_id == trade_id
    assert trades[0].symbol == "BTCUSDT"
    assert trades[0].ts_close is None


def test_record_close_updates_row_and_computes_pnl(tmp_path) -> None:
    db_path = tmp_path / "perf.sqlite3"
    store = PerformanceStore(db_path)
    store.init_db()

    trade_id = store.record_open(
        TradeOpenEvent(
            ts_open="2025-01-01T00:00:00+00:00",
            symbol="BTCUSDT",
            side="BUY",
            qty=2.0,
            entry_price=100.0,
        )
    )

    store.record_close(
        trade_id,
        TradeCloseEvent(
            ts_close="2025-01-01T01:00:00+00:00",
            exit_price=110.0,
            fees=1.0,
            reason_close="tp",
        ),
    )

    trade = store.get_trades()[0]
    assert trade.ts_close == "2025-01-01T01:00:00+00:00"
    assert trade.exit_price == 110.0
    assert trade.fees == 1.0
    assert trade.pnl_usdt == 19.0
    assert trade.pnl_pct == 9.5
