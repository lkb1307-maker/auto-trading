from __future__ import annotations

from src.app.state import BotState


def test_bot_state_defaults() -> None:
    state = BotState()

    assert state.tick_count == 0
    assert state.last_tick_at is None
    assert state.positions == {}
    assert state.started_at is not None


def test_mark_tick_updates_counter_and_timestamp() -> None:
    state = BotState()

    state.mark_tick()

    assert state.tick_count == 1
    assert state.last_tick_at is not None
