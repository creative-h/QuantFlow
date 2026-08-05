"""Live Market Service orchestrating KiteFeed, TickCache, and CandleBuilder."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

from loguru import logger

from app.marketdata.candle_builder import CandleBuilder
from app.marketdata.kite_feed import KiteTickerFeedManager
from app.marketdata.live_feed import Tick
from app.marketdata.tick_cache import TickCache
from app.models.dataclasses import Candle


@dataclass
class InstrumentSnapshot:
    """Dataclass holding real-time instrument market snapshot."""

    symbol: str
    price: float
    previous_price: float
    change_pct: float
    volume: int
    latency_ms: float
    last_update: datetime
    candle_countdown_sec: int


class LiveMarketService:
    """Central Live Market Service owning WebSocket Feed, Tick Cache, and Candle Builder."""

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        feed_manager: Optional[KiteTickerFeedManager] = None,
        candle_builder: Optional[CandleBuilder] = None,
        tick_cache: Optional[TickCache] = None,
    ) -> None:
        self.symbols = symbols or ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        self.tick_cache = tick_cache or TickCache()
        self.feed_manager = feed_manager or KiteTickerFeedManager(symbols=self.symbols, tick_cache=self.tick_cache)
        self.candle_builder = candle_builder or CandleBuilder()

        # Connect feed ticks to candle builder
        self.feed_manager.register_listener(self.candle_builder.process_tick)

    def start(self) -> None:
        """Start Live Market Service lifecycle."""
        self.feed_manager.start()
        logger.info("LiveMarketService started")

    def stop(self) -> None:
        """Stop Live Market Service lifecycle."""
        self.feed_manager.stop()
        logger.info("LiveMarketService stopped")

    def register_candle_listener(self, callback: Callable[[str, str, Candle], None]) -> None:
        """Register callback for completed candle emissions."""
        self.candle_builder.register_listener(callback)

    def register_tick_listener(self, callback: Callable[[Tick], None]) -> None:
        """Register callback for real-time tick emissions."""
        self.feed_manager.register_listener(callback)

    def get_market_snapshot(self, symbol: str) -> Optional[InstrumentSnapshot]:
        """Return real-time market snapshot for an instrument."""
        sym_clean = symbol.upper()
        latest = self.tick_cache.get_latest(sym_clean)
        prev = self.tick_cache.get_previous(sym_clean)

        if not latest:
            return None

        prev_price = prev.price if prev else latest.open or latest.price
        change_pct = round(((latest.price - prev_price) / prev_price) * 100.0, 2) if prev_price > 0 else 0.0
        latency = self.tick_cache.get_latency_ms(sym_clean)
        last_update = self.tick_cache.get_last_update_timestamp(sym_clean) or datetime.now()

        # Compute 1m candle countdown in seconds
        now_epoch = int(datetime.now().timestamp())
        next_bar_epoch = ((now_epoch // 60) + 1) * 60
        countdown = max(0, next_bar_epoch - now_epoch)

        return InstrumentSnapshot(
            symbol=sym_clean,
            price=latest.price,
            previous_price=prev_price,
            change_pct=change_pct,
            volume=latest.volume,
            latency_ms=latency,
            last_update=last_update,
            candle_countdown_sec=countdown,
        )

    def get_all_snapshots(self) -> Dict[str, InstrumentSnapshot]:
        """Return market snapshots for all subscribed instruments."""
        snapshots = {}
        for sym in self.symbols:
            snap = self.get_market_snapshot(sym)
            if snap:
                snapshots[sym] = snap
        return snapshots
