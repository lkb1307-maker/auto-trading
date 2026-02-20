from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Protocol


class Notifier(Protocol):
    def send_message(self, text: str) -> bool: ...


class TelegramNotifier:
    def __init__(
        self, token: str | None, chat_id: str | None, logger: logging.Logger
    ) -> None:
        self.token = token
        self.chat_id = chat_id
        self.logger = logger

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.enabled:
            self.logger.warning(
                "Telegram notifier disabled: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing"
            )
            return False

        payload = {"chat_id": self.chat_id, "text": text}
        if importlib.util.find_spec("requests") is not None:
            requests = importlib.import_module("requests")
            return self._send_with_requests(requests_module=requests, payload=payload)

        self.logger.warning(
            "requests is not installed; using urllib fallback for Telegram"
        )
        return self._send_with_urllib(payload=payload)

    def _send_with_requests(
        self, requests_module: Any, payload: dict[str, str | None]
    ) -> bool:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        response = requests_module.post(url, json=payload, timeout=10)
        if response.ok:
            return True

        self.logger.warning(
            "Telegram API responded with status %s", response.status_code
        )
        return False

    def _send_with_urllib(self, payload: dict[str, str | None]) -> bool:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                success = 200 <= response.status < 300
                if not success:
                    self.logger.warning(
                        "Telegram API responded with status %s", response.status
                    )
                return success
        except urllib.error.URLError as exc:
            self.logger.warning("Telegram message failed: %s", exc)
            return False
