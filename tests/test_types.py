from __future__ import annotations

from src.app.types import Signal


def test_signal_is_string_enum() -> None:
    assert isinstance(Signal.LONG, str)
    assert Signal.LONG == "long"
