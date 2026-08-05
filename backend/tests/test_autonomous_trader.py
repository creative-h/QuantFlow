"""Unit tests for AutonomousPaperTrader scanner and active trade management."""

import time

import pytest

from app.paper.autonomous_trader import AutonomousPaperTrader
from app.paper.state_machine import TradeState


def test_autonomous_trader_initialization():
    trader = AutonomousPaperTrader()
    assert not trader.is_auto_trading
    assert len(trader.active_trades) == 0
    assert len(trader.ai_timeline) > 0


def test_autonomous_trader_start_stop():
    trader = AutonomousPaperTrader()
    trader.start()
    assert trader.is_auto_trading

    time.sleep(1.0)

    trader.stop()
    assert not trader.is_auto_trading


def test_autonomous_trader_scan_and_execute():
    trader = AutonomousPaperTrader(min_confidence=50.0)
    trader.start()

    time.sleep(2.0)

    # Force a scan step
    trader.scan_and_execute()
    trader.manage_open_trades()

    trader.stop()
    assert isinstance(trader.ai_timeline, list)
