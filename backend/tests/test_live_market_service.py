"""Unit tests for LiveMarketService orchestrator."""

import time

import pytest

from app.services.live_market_service import InstrumentSnapshot, LiveMarketService


def test_live_market_service_initialization():
    service = LiveMarketService(symbols=["NIFTY", "BANKNIFTY"])
    assert service.symbols == ["NIFTY", "BANKNIFTY"]
    assert service.feed_manager is not None
    assert service.candle_builder is not None
    assert service.tick_cache is not None


def test_live_market_service_start_stop_snapshot():
    service = LiveMarketService(symbols=["NIFTY", "BANKNIFTY"])
    service.start()

    time.sleep(1.5)

    snap_nifty = service.get_market_snapshot("NIFTY")
    assert snap_nifty is not None
    assert isinstance(snap_nifty, InstrumentSnapshot)
    assert snap_nifty.symbol == "NIFTY"
    assert snap_nifty.price > 0.0
    assert snap_nifty.candle_countdown_sec >= 0

    all_snaps = service.get_all_snapshots()
    assert "NIFTY" in all_snaps
    assert "BANKNIFTY" in all_snaps

    service.stop()


def test_instrument_snapshot_dataclass():
    from datetime import datetime
    snap = InstrumentSnapshot(
        symbol="FINNIFTY",
        price=22450.0,
        previous_price=22400.0,
        change_pct=0.22,
        volume=15000,
        latency_ms=10.5,
        last_update=datetime.now(),
        candle_countdown_sec=45,
    )
    assert snap.symbol == "FINNIFTY"
    assert snap.change_pct == 0.22
    assert snap.candle_countdown_sec == 45
