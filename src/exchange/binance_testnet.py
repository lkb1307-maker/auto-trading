from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from urllib import error, parse, request

from src.config.settings import Settings
from src.exchange.base import (
    Balance,
    Candle,
    ExchangeClient,
    OrderRequest,
    OrderResult,
    PositionSummary,
    PriceQuote,
)


class ExchangeError(RuntimeError):
    """Base exchange adapter error."""


class ExchangeAuthError(ExchangeError):
    """Authentication-related exchange error."""


class ExchangeRateLimitError(ExchangeError):
    """Rate limit exchange error."""


class BinanceFuturesTestnetClient(ExchangeClient):
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.base_url = settings.binance_base_url.rstrip("/")
        self.recv_window = settings.binance_recv_window
        self._timeout_seconds = 10
        self._max_retries = 2

    def get_mark_price(self, symbol: str) -> PriceQuote:
        response = self._request("GET", "/fapi/v1/premiumIndex", {"symbol": symbol})
        return PriceQuote(
            symbol=response["symbol"],
            mark_price=Decimal(response["markPrice"]),
            event_time=datetime.now(tz=timezone.utc),  # noqa: UP017
        )

    def get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        response = self._request(
            "GET",
            "/fapi/v1/klines",
            {"symbol": symbol, "interval": timeframe, "limit": limit},
        )
        return [self._to_candle(candle_data) for candle_data in response]

    def get_balances(self) -> list[Balance]:
        if not self._can_use_signed_endpoints():
            return []

        response = self._request("GET", "/fapi/v2/balance", signed=True)
        return [
            Balance(
                asset=item["asset"],
                wallet_balance=Decimal(item["balance"]),
                available_balance=Decimal(item["availableBalance"]),
            )
            for item in response
        ]

    def get_positions(self, symbol: str | None = None) -> list[PositionSummary]:
        if not self._can_use_signed_endpoints():
            return []

        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol

        response = self._request("GET", "/fapi/v2/positionRisk", params, signed=True)
        return [
            PositionSummary(
                symbol=item["symbol"],
                position_amt=Decimal(item["positionAmt"]),
                entry_price=Decimal(item["entryPrice"]),
                unrealized_pnl=Decimal(item["unRealizedProfit"]),
                leverage=int(item["leverage"]),
            )
            for item in response
            if Decimal(item["positionAmt"]) != 0
        ]

    def place_order(self, order: OrderRequest) -> OrderResult:
        if self.settings.dry_run:
            self.logger.info(
                "dry-run mock order",
                extra={
                    "symbol": order.symbol,
                    "side": order.side,
                    "order_type": order.order_type,
                    "quantity": str(order.quantity),
                },
            )
            mock_id = f"dryrun-{int(time.time() * 1000)}"
            return OrderResult(
                status="MOCK_FILLED",
                symbol=order.symbol,
                order_id=mock_id,
                client_order_id="DRY_RUN",
            )

        raise ExchangeError(
            "Real order placement is intentionally disabled in Milestone B."
        )

    def _can_use_signed_endpoints(self) -> bool:
        has_key = bool(self.settings.binance_api_key)
        has_secret = bool(self.settings.binance_secret_key)

        if has_key and has_secret:
            return True

        if self.settings.dry_run:
            self.logger.warning(
                "Missing Binance API credentials in DRY_RUN mode; "
                "using safe empty signed endpoint fallback"
            )
            return False

        raise ExchangeAuthError(
            "BINANCE_API_KEY and BINANCE_SECRET_KEY are required "
            "for signed endpoints when DRY_RUN=0."
        )

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> Any:
        query_params = dict(params or {})
        headers = {"Content-Type": "application/json"}

        if signed:
            query_params["timestamp"] = int(time.time() * 1000)
            query_params["recvWindow"] = self.recv_window
            payload = self._encode_params(query_params)
            query_params["signature"] = self._build_signature(payload)
            headers["X-MBX-APIKEY"] = self.settings.binance_api_key or ""

        query = self._encode_params(query_params)
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"

        self.logger.debug(
            "exchange request",
            extra={"method": method, "path": path, "signed": signed},
        )

        attempt = 0
        while True:
            try:
                req = request.Request(url=url, method=method, headers=headers)
                with request.urlopen(req, timeout=self._timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                return json.loads(body)
            except error.HTTPError as exc:
                body = exc.read().decode("utf-8") if exc.fp is not None else ""
                if exc.code == 401:
                    raise ExchangeAuthError("Binance authentication failed") from exc
                if exc.code == 429:
                    raise ExchangeRateLimitError("Binance rate limit exceeded") from exc
                if exc.code >= 500 and attempt < self._max_retries:
                    attempt += 1
                    time.sleep(0.2 * attempt)
                    continue
                raise ExchangeError(
                    f"Binance request failed with status {exc.code}: {body[:200]}"
                ) from exc
            except error.URLError as exc:
                if attempt < self._max_retries:
                    attempt += 1
                    time.sleep(0.2 * attempt)
                    continue
                raise ExchangeError(f"Binance network error: {exc.reason}") from exc

    def _build_signature(self, payload: str) -> str:
        if not self.settings.binance_secret_key:
            raise ExchangeAuthError(
                "BINANCE_SECRET_KEY is required for signed requests"
            )

        digest = hmac.new(
            self.settings.binance_secret_key.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        )
        return digest.hexdigest()

    @staticmethod
    def _encode_params(params: dict[str, Any]) -> str:
        normalized = {key: str(value) for key, value in params.items()}
        return parse.urlencode(sorted(normalized.items()))

    @staticmethod
    def _to_candle(item: list[Any]) -> Candle:
        return Candle(
            open_time=datetime.fromtimestamp(
                int(item[0]) / 1000,
                tz=timezone.utc,  # noqa: UP017
            ),
            open_price=Decimal(item[1]),
            high_price=Decimal(item[2]),
            low_price=Decimal(item[3]),
            close_price=Decimal(item[4]),
            volume=Decimal(item[5]),
            close_time=datetime.fromtimestamp(
                int(item[6]) / 1000,
                tz=timezone.utc,  # noqa: UP017
            ),
        )
