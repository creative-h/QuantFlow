"""Unit tests for production WebSocketManager."""

import time
import pytest

from app.marketdata.live_feed import Tick
from app.marketdata.websocket_manager import WebSocketManager


def test_websocket_manager_connect_disconnect():
    wm = WebSocketManager()
    assert not wm.is_connected()

    wm.connect()
    assert wm._is_running

    time.sleep(1.2)
    assert wm.is_connected()

    tick = wm.latest_tick("NIFTY")
    assert tick is not None
    assert tick.symbol == "NIFTY"
    assert tick.price > 0.0

    wm.disconnect()
    assert not wm._is_running


def test_websocket_manager_subscribe_unsubscribe():
    wm = WebSocketManager()
    wm.subscribe(12345)
    assert 12345 in wm._subscribed_tokens

    wm.subscribe([67890, 99999])
    assert 67890 in wm._subscribed_tokens

    wm.unsubscribe(12345)
    assert 12345 not in wm._subscribed_tokens


def test_websocket_manager_listener_callback():
    ticks = []

    def on_tick(t: Tick):
        ticks.append(t)

    wm = WebSocketManager()
    wm.register_listener(on_tick)
    wm.connect()
    time.sleep(1.2)

    assert len(ticks) > 0
    wm.disconnect()
