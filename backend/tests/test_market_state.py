"""Unit tests for MarketStateEngine."""

from datetime import datetime
import pytest

from app.marketdata.market_state import MarketStateEngine, MarketStatusInfo


def test_market_state_open_session():
    # Wednesday 11:30 AM
    dt = datetime(2026, 4, 15, 11, 30, 0)
    info = MarketStateEngine.get_market_state(dt)
    assert info.status == "OPEN"
    assert info.is_trading_day
    assert not info.is_weekend
    assert not info.is_holiday


def test_market_state_preopen_session():
    # Wednesday 9:05 AM
    dt = datetime(2026, 4, 15, 9, 5, 0)
    info = MarketStateEngine.get_market_state(dt)
    assert info.status == "PREOPEN"


def test_market_state_post_market_session():
    # Wednesday 3:45 PM
    dt = datetime(2026, 4, 15, 15, 45, 0)
    info = MarketStateEngine.get_market_state(dt)
    assert info.status == "POST MARKET"


def test_market_state_closed_weekend():
    # Saturday 12:00 PM
    dt = datetime(2026, 4, 18, 12, 0, 0)
    info = MarketStateEngine.get_market_state(dt)
    assert info.status == "CLOSED"
    assert info.is_weekend


def test_market_state_holiday():
    # Republic Day Jan 26, 2026
    dt = datetime(2026, 1, 26, 11, 0, 0)
    info = MarketStateEngine.get_market_state(dt)
    assert info.status == "CLOSED"
    assert info.is_holiday
    assert info.holiday_name == "Republic Day"
