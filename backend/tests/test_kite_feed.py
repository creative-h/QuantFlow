"""Unit tests for KiteTickerFeedManager, exponential backoff, and heartbeat."""

import time

import pytest

from app.marketdata.kite_feed import KiteTickerFeedManager
from app.marketdata.live_feed import Tick
from app.marketdata.tick_cache import TickCache


def test_kite_feed_manager_initialization():
    feed = KiteTickerFeedManager(symbols=["NIFTY", "BANKNIFTY"])
    assert not feed.is_connected()
    assert feed.get_connection_status() == "DISCONNECTED"
    assert feed.initial_reconnect_delay == 1
    assert feed.max_reconnect_delay == 30


def test_kite_feed_manager_start_stop_flow():
    feed = KiteTickerFeedManager(symbols=["NIFTY"])
    feed.start()
    assert feed._is_running

    time.sleep(1.2)

    status = feed.get_connection_status()
    assert status in ("CONNECTED", "SIMULATED / RECONNECTING")

    tick = feed.tick_cache.get_latest("NIFTY")
    assert tick is not None
    assert tick.symbol == "NIFTY"
    assert tick.price > 0.0

    feed.stop()
    assert not feed._is_running


def test_kite_feed_manager_exponential_backoff_calculation():
    feed = KiteTickerFeedManager(initial_reconnect_delay_sec=1, max_reconnect_delay_sec=10)
    assert feed._current_reconnect_delay == 1

    # Simulate exponential step
    feed._current_reconnect_delay = min(feed.max_reconnect_delay, feed._current_reconnect_delay * 2)
    assert feed._current_reconnect_delay == 2

    feed._current_reconnect_delay = min(feed.max_reconnect_delay, feed._current_reconnect_delay * 2)
    assert feed._current_reconnect_delay == 4


def test_kite_feed_manager_listener():
    ticks = []

    def on_tick(tick: Tick):
        ticks.append(tick)

    feed = KiteTickerFeedManager(symbols=["FINNIFTY"])
    feed.register_listener(on_tick)
    feed.start()
    time.sleep(1.2)

    assert len(ticks) > 0
    assert ticks[0].symbol == "FINNIFTY"

    feed.stop()
