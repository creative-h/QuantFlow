"""Unit tests for QuantFlow v9.0 Market Replay Simulator Engine."""

import pytest

from app.simulation.replay_engine import MarketReplayEngine, ReplayOrder, ReplayState


def test_market_replay_engine_initialization():
    engine = MarketReplayEngine(symbol="NIFTY")
    state = engine.get_state()
    assert isinstance(state, ReplayState)
    assert state.symbol == "NIFTY"
    assert state.current_index == 10
    assert state.status == "IDLE"
    assert state.speed_multiplier == 1.0


def test_market_replay_engine_step_forward_and_backward():
    engine = MarketReplayEngine(symbol="BANKNIFTY")
    initial_idx = engine.current_index

    # Step forward by 2 bars
    state = engine.step_forward(2)
    assert engine.current_index == initial_idx + 2
    assert state.current_candle is not None

    # Step backward by 1 bar
    state = engine.step_backward(1)
    assert engine.current_index == initial_idx + 1


def test_market_replay_engine_speed_multiplier():
    engine = MarketReplayEngine(symbol="NIFTY")
    engine.set_speed(10.0)
    assert engine.speed_multiplier == 10.0

    engine.set_speed(100.0)
    assert engine.speed_multiplier == 100.0


def test_market_replay_engine_play_pause_flow():
    engine = MarketReplayEngine(symbol="NIFTY")
    engine.play()
    assert engine.status == "PLAYING"

    engine.pause()
    assert engine.status == "PAUSED"
