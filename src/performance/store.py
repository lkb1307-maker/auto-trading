from __future__ import annotations

import logging
import sqlite3
import uuid
from pathlib import Path

from .models import TradeCloseEvent, TradeOpenEvent, TradeRecord

LOGGER = logging.getLogger(__name__)


class PerformanceStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    ts_open TEXT NOT NULL,
                    ts_close TEXT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NULL,
                    fees REAL NULL,
                    pnl_usdt REAL NULL,
                    pnl_pct REAL NULL,
                    reason_open TEXT NULL,
                    reason_close TEXT NULL,
                    strategy_name TEXT NULL,
                    strategy_version TEXT NULL,
                    mode TEXT NULL,
                    exchange_order_ids TEXT NULL,
                    meta_json TEXT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_ts_open ON trades(ts_open)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_ts_close ON trades(ts_close)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_strategy_name "
                "ON trades(strategy_name)"
            )
            conn.commit()
        LOGGER.info(
            "performance store initialized", extra={"db_path": str(self.db_path)}
        )

    def record_open(self, event: TradeOpenEvent) -> str:
        trade_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO trades (
                    trade_id, ts_open, symbol, side, qty, entry_price,
                    reason_open, strategy_name, strategy_version, mode,
                    exchange_order_ids, meta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_id,
                    event.ts_open,
                    event.symbol,
                    event.side,
                    event.qty,
                    event.entry_price,
                    event.reason_open,
                    event.strategy_name,
                    event.strategy_version,
                    event.mode,
                    event.exchange_order_ids,
                    event.meta_json,
                ),
            )
            conn.commit()
        LOGGER.info(
            "trade open recorded", extra={"trade_id": trade_id, "symbol": event.symbol}
        )
        return trade_id

    def record_close(self, trade_id: str, event: TradeCloseEvent) -> None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT side, qty, entry_price FROM trades WHERE trade_id = ?",
                (trade_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Trade not found: {trade_id}")

            side, qty, entry_price = row
            fees = event.fees if event.fees is not None else 0.0
            pnl_usdt = event.pnl_usdt
            pnl_pct = event.pnl_pct

            if (
                pnl_usdt is None
                and event.exit_price is not None
                and entry_price is not None
            ):
                raw_delta = float(event.exit_price) - float(entry_price)
                direction = 1.0 if str(side).upper() == "BUY" else -1.0
                pnl_usdt = (raw_delta * direction * float(qty)) - fees

            if pnl_pct is None and pnl_usdt is not None and entry_price:
                notional = float(entry_price) * float(qty)
                if notional != 0:
                    pnl_pct = (pnl_usdt / notional) * 100.0

            conn.execute(
                """
                UPDATE trades
                SET ts_close = ?,
                    exit_price = ?,
                    fees = ?,
                    pnl_usdt = ?,
                    pnl_pct = ?,
                    reason_close = ?,
                    exchange_order_ids = COALESCE(?, exchange_order_ids),
                    meta_json = COALESCE(?, meta_json)
                WHERE trade_id = ?
                """,
                (
                    event.ts_close,
                    event.exit_price,
                    fees,
                    pnl_usdt,
                    pnl_pct,
                    event.reason_close,
                    event.exchange_order_ids,
                    event.meta_json,
                    trade_id,
                ),
            )
            conn.commit()
        LOGGER.info("trade close recorded", extra={"trade_id": trade_id})

    def get_trades(
        self,
        time_min: str | None = None,
        time_max: str | None = None,
        strategy_name: str | None = None,
        mode: str | None = None,
    ) -> list[TradeRecord]:
        query = "SELECT * FROM trades WHERE 1=1"
        params: list[object] = []
        if time_min:
            query += " AND ts_open >= ?"
            params.append(time_min)
        if time_max:
            query += " AND ts_open <= ?"
            params.append(time_max)
        if strategy_name:
            query += " AND strategy_name = ?"
            params.append(strategy_name)
        if mode:
            query += " AND mode = ?"
            params.append(mode)
        query += " ORDER BY ts_open ASC"

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()

        return [TradeRecord(*row) for row in rows]
