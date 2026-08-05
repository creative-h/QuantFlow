"""Memory-resident Tick Cache storing instrument token, symbol, price, bid/ask, OHLC, OI, and change."""

from dataclasses import dataclass, field
from datetime import datetime
import threading
from typing import Dict, List, Optional, Union

from app.marketdata.live_feed import Tick


@dataclass
class CachedTickEntry:
    """Dataclass storing comprehensive tick telemetry."""

    instrument_token: int = 0
    symbol: str = ""
    last_price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    volume: int = 0
    oi: int = 0
    ohlc: Dict[str, float] = field(default_factory=dict)
    change: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    latest_tick: Optional[Tick] = None
    previous_tick: Optional[Tick] = None
    latency_ms: float = 0.0


class TickCache:
    """Thread-safe memory cache storing live ticks for instant UI and AI retrieval."""

    SYMBOL_TOKEN_MAP = {
        "NIFTY": 256265,
        "BANKNIFTY": 260105,
        "FINNIFTY": 257001,
        "MIDCPNIFTY": 288009,
        "SENSEX": 265,
    }
    TOKEN_SYMBOL_MAP = {v: k for k, v in SYMBOL_TOKEN_MAP.items()}

    def __init__(self) -> None:
        self._cache_by_symbol: Dict[str, CachedTickEntry] = {}
        self._cache_by_token: Dict[int, CachedTickEntry] = {}
        self._lock = threading.Lock()

    def update_tick(self, tick: Tick) -> None:
        """Update cache entry instantly when a new websocket tick arrives."""
        sym_clean = tick.symbol.upper()
        token = self.SYMBOL_TOKEN_MAP.get(sym_clean, 999999)
        now = tick.timestamp or datetime.now()

        bid_p = round(tick.price - 0.05, 2)
        ask_p = round(tick.price + 0.05, 2)
        open_p = tick.open if tick.open else tick.price
        change_val = round(tick.price - open_p, 2)
        ohlc_dict = {"open": open_p, "high": tick.high, "low": tick.low, "close": tick.close}

        latency = (datetime.now() - now).total_seconds() * 1000.0
        latency = round(max(0.0, latency), 2)

        with self._lock:
            existing = self._cache_by_symbol.get(sym_clean)
            prev_t = existing.latest_tick if existing else None

            entry = CachedTickEntry(
                instrument_token=token,
                symbol=sym_clean,
                last_price=tick.price,
                bid=bid_p,
                ask=ask_p,
                volume=tick.volume,
                oi=tick.oi,
                ohlc=ohlc_dict,
                change=change_val,
                timestamp=now,
                latest_tick=tick,
                previous_tick=prev_t,
                latency_ms=latency,
            )

            self._cache_by_symbol[sym_clean] = entry
            self._cache_by_token[token] = entry

    def get_tick(self, symbol_or_token: Union[str, int]) -> Optional[Tick]:
        """Thread-safe retrieval of latest tick by symbol or instrument token."""
        with self._lock:
            if isinstance(symbol_or_token, int):
                entry = self._cache_by_token.get(symbol_or_token)
            else:
                entry = self._cache_by_symbol.get(str(symbol_or_token).upper())
            return entry.latest_tick if entry else None

    def get_tick_entry(self, symbol_or_token: Union[str, int]) -> Optional[CachedTickEntry]:
        """Thread-safe retrieval of detailed CachedTickEntry."""
        with self._lock:
            if isinstance(symbol_or_token, int):
                return self._cache_by_token.get(symbol_or_token)
            else:
                return self._cache_by_symbol.get(str(symbol_or_token).upper())

    def get_latest(self, symbol: str) -> Optional[Tick]:
        """Backward compatible getter for latest tick."""
        return self.get_tick(symbol)

    def get_previous(self, symbol: str) -> Optional[Tick]:
        """Backward compatible getter for previous tick."""
        entry = self.get_tick_entry(symbol)
        return entry.previous_tick if entry else None

    def get_latency_ms(self, symbol: str) -> float:
        """Backward compatible getter for latency in ms."""
        entry = self.get_tick_entry(symbol)
        return entry.latency_ms if entry else 0.0

    def get_last_update_timestamp(self, symbol: str) -> Optional[datetime]:
        """Backward compatible getter for last update timestamp."""
        entry = self.get_tick_entry(symbol)
        return entry.timestamp if entry else None

    def get_all(self) -> Dict[str, CachedTickEntry]:
        """Thread-safe retrieval of all cached tick entries."""
        with self._lock:
            return dict(self._cache_by_symbol)

    def get_all_latest(self) -> Dict[str, Tick]:
        """Thread-safe retrieval of all latest ticks."""
        with self._lock:
            return {sym: entry.latest_tick for sym, entry in self._cache_by_symbol.items() if entry.latest_tick is not None}

    def clear(self) -> None:
        """Clear memory tick cache."""
        with self._lock:
            self._cache_by_symbol.clear()
            self._cache_by_token.clear()
