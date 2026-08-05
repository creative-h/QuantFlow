"""Unit tests for KiteLiveFeedManager and Tick dataclass."""

from datetime import datetime
import time

import pytest

from app.marketdata.live_feed import KiteLiveFeedManager, Tick


def test_tick_dataclass_initialization():
    tick = Tick(symbol="NIFTY", price=24915.20, volume=1500)
    assert tick.symbol == "NIFTY"
    assert tick.price == 24915.20
    assert tick.volume == 1500
    assert isinstance(tick.timestamp, datetime)


def test_live_feed_manager_start_and_stop():
    feed = KiteLiveFeedManager(symbols=["NIFTY", "BANKNIFTY"])
    assert not feed._is_running

    feed.start()
    assert feed._is_running

    time.sleep(1.5)

    tick_nifty = feed.get_latest_tick("NIFTY")
    assert tick_nifty is not None
    assert tick_nifty.symbol == "NIFTY"
    assert tick_nifty.price > 0.0

    feed.stop()
    assert not feed._is_running


def test_live_feed_manager_get_all_ticks():
    feed = KiteLiveFeedManager(symbols=["NIFTY", "BANKNIFTY"])
    feed.start()
    time.sleep(1.5)

    ticks = feed.get_all_ticks()
    assert "NIFTY" in ticks
    assert "BANKNIFTY" in ticks

    feed.stop()


def test_live_feed_manager_listener_callback():
    received_ticks = []

    def on_tick(tick: Tick):
        received_ticks.append(tick)

    feed = KiteLiveFeedManager(symbols=["NIFTY"])
    feed.register_listener(on_tick)
    feed.start()
    time.sleep(1.5)

    assert len(received_ticks) > 0
    assert received_ticks[0].symbol == "NIFTY"

    feed.stop()
