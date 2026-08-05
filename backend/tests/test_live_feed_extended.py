"""Extended Unit Tests for KiteLiveFeedManager thread safety and symbol management."""

import time
import pytest
from app.marketdata.live_feed import KiteLiveFeedManager, Tick


def test_live_feed_custom_symbols():
    feed = KiteLiveFeedManager(symbols=["FINNIFTY", "MIDCPNIFTY", "SENSEX"])
    feed.start()
    time.sleep(1.2)

    tick_fin = feed.get_latest_tick("FINNIFTY")
    assert tick_fin is not None
    assert tick_fin.symbol == "FINNIFTY"

    tick_mid = feed.get_latest_tick("MIDCPNIFTY")
    assert tick_mid is not None
    assert tick_mid.symbol == "MIDCPNIFTY"

    tick_sensex = feed.get_latest_tick("SENSEX")
    assert tick_sensex is not None
    assert tick_sensex.symbol == "SENSEX"

    feed.stop()


def test_live_feed_double_start_stop_safe():
    feed = KiteLiveFeedManager(symbols=["NIFTY"])
    feed.start()
    feed.start()  # Idempotent start call
    assert feed._is_running

    time.sleep(1.0)
    feed.stop()
    feed.stop()  # Idempotent stop call
    assert not feed._is_running


def test_live_feed_heartbeat_timestamp():
    feed = KiteLiveFeedManager(symbols=["NIFTY"])
    feed.start()
    time.sleep(1.2)
    assert feed._last_heartbeat is not None
    feed.stop()
