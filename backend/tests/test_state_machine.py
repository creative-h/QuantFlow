"""Unit tests for TradeStateMachine and 8-State lifecycle transitions."""

import pytest

from app.paper.state_machine import TradeState, TradeStateMachine


def test_state_machine_initialization():
    sm = TradeStateMachine(trade_id="TRADE_101", initial_state=TradeState.WAITING)
    assert sm.trade_id == "TRADE_101"
    assert sm.current_state == TradeState.WAITING
    assert len(sm.history) == 0


def test_valid_state_transitions():
    sm = TradeStateMachine(trade_id="TRADE_101", initial_state=TradeState.WAITING)

    # WAITING -> WATCHLIST
    assert sm.transition_to(TradeState.WATCHLIST, reason="Setup identified")
    assert sm.current_state == TradeState.WATCHLIST

    # WATCHLIST -> READY
    assert sm.transition_to(TradeState.READY, reason="Pre-trade check passed")
    assert sm.current_state == TradeState.READY

    # READY -> ENTERED
    assert sm.transition_to(TradeState.ENTERED, reason="Order filled")
    assert sm.current_state == TradeState.ENTERED

    # ENTERED -> PARTIAL_EXIT
    assert sm.transition_to(TradeState.PARTIAL_EXIT, reason="Target 1 hit")
    assert sm.current_state == TradeState.PARTIAL_EXIT

    # PARTIAL_EXIT -> TRAILING
    assert sm.transition_to(TradeState.TRAILING, reason="Trailing active")
    assert sm.current_state == TradeState.TRAILING

    # TRAILING -> EXITED
    assert sm.transition_to(TradeState.EXITED, reason="Final exit")
    assert sm.current_state == TradeState.EXITED

    assert len(sm.history) == 6


def test_invalid_state_transition_prevented():
    sm = TradeStateMachine(trade_id="TRADE_102", initial_state=TradeState.WAITING)

    # WAITING cannot transition directly to EXITED
    success = sm.transition_to(TradeState.EXITED, reason="Direct exit attempt")
    assert not success
    assert sm.current_state == TradeState.WAITING
    assert len(sm.history) == 0
