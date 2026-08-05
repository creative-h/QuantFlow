"""QuantFlow v3.0 Sprint 1 Comprehensive Test Suite."""

from datetime import datetime
from pathlib import Path
import yaml
import pytest

from app.marketdata.candle_builder import CandleBuilder
from app.marketdata.kite_feed import KiteTickerFeedManager
from app.marketdata.live_feed import Tick
from app.marketdata.tick_cache import CachedTickEntry, TickCache
from app.services.live_market_service import InstrumentSnapshot, LiveMarketService


def test_v30_websocket_yaml_loading():
    path = Path(__file__).parent.parent / "config" / "websocket.yaml"
    assert path.exists()
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    assert "websocket" in cfg
    assert cfg["websocket"]["reconnect_initial_delay_sec"] == 1
    assert cfg["websocket"]["instruments"]["NIFTY"] == 256265


def test_v30_tick_cache_multiple_instruments():
    cache = TickCache()
    cache.update_tick(Tick("NIFTY", 24900.0, 100))
    cache.update_tick(Tick("BANKNIFTY", 55000.0, 200))
    cache.update_tick(Tick("FINNIFTY", 22400.0, 300))

    assert cache.get_latest("NIFTY").price == 24900.0
    assert cache.get_latest("BANKNIFTY").price == 55000.0
    assert cache.get_latest("FINNIFTY").price == 22400.0


def test_v30_kite_feed_connection_status_strings():
    feed = KiteTickerFeedManager(symbols=["NIFTY"])
    assert feed.get_connection_status() == "DISCONNECTED"

    feed._is_running = True
    feed._is_connected = True
    assert feed.get_connection_status() == "CONNECTED"

    feed._is_connected = False
    assert feed.get_connection_status() == "SIMULATED / RECONNECTING"


def test_v30_live_market_service_listeners():
    emitted_candles = []
    emitted_ticks = []

    def on_c(sym, tf, c):
        emitted_candles.append((sym, tf, c))

    def on_t(t):
        emitted_ticks.append(t)

    svc = LiveMarketService(symbols=["NIFTY"])
    svc.register_candle_listener(on_c)
    svc.register_tick_listener(on_t)

    svc.start()
    import time
    time.sleep(1.2)

    assert len(emitted_ticks) > 0
    svc.stop()


def test_v30_snapshot_calculation():
    cache = TickCache()
    t1 = Tick("NIFTY", 24900.0, 100, datetime.now())
    t2 = Tick("NIFTY", 24950.0, 150, datetime.now())
    cache.update_tick(t1)
    cache.update_tick(t2)

    svc = LiveMarketService(symbols=["NIFTY"], tick_cache=cache)
    snap = svc.get_market_snapshot("NIFTY")

    assert snap is not None
    assert snap.price == 24950.0
    assert snap.previous_price == 24900.0
    assert snap.change_pct == 0.20
