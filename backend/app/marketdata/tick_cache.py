"""Thread-safe Tick Cache storing latest tick, previous tick, timestamp, and latency per instrument."""

from dataclasses import dataclass, field
from datetime import datetime
import threading
from typing import Dict, Optional

from app.marketdata.live_feed import Tick


@dataclass
class CachedTickEntry:
    """Dataclass storing cached latest tick, previous tick, and latency metrics."""

    symbol: str
    latest_tick: Optional[Tick] = None
    previous_tick: Optional[Tick] = None
    last_update_timestamp: Optional[datetime] = None
    latency_ms: float = 0.0


class TickCache:
    """Thread-safe Tick Cache maintaining price tick history and update latency per instrument."""

    def __init__(self) -> None:
        self._cache: Dict[str, CachedTickEntry] = {}
        self._lock = threading.Lock()

    def update_tick(self, tick: Tick) -> None:
        """Update cache entry with new tick, shifting previous tick and computing latency."""
        sym_clean = tick.symbol.upper()
        now = datetime.now()

        # Calculate tick latency in milliseconds
        latency = (now - tick.timestamp).total_seconds() * 1000.0 if tick.timestamp else 0.0
        latency = round(max(0.0, latency), 2)

        with self._lock:
            entry = self._cache.get(sym_clean)
            if entry is None:
                entry = CachedTickEntry(
                    symbol=sym_clean,
                    latest_tick=tick,
                    previous_tick=None,
                    last_update_timestamp=now,
                    latency_ms=latency,
                )
                self._cache[sym_clean] = entry
            else:
                entry.previous_tick = entry.latest_tick
                entry.latest_tick = tick
                entry.last_update_timestamp = now
                entry.latency_ms = latency

    def get_latest(self, symbol: str) -> Optional[Tick]:
        """Thread-safe retrieval of latest tick for a symbol."""
        with self._lock:
            entry = self._cache.get(symbol.upper())
            return entry.latest_tick if entry else None

    def get_previous(self, symbol: str) -> Optional[Tick]:
        """Thread-safe retrieval of previous tick for a symbol."""
        with self._lock:
            entry = self._cache.get(symbol.upper())
            return entry.previous_tick if entry else None

    def get_latency_ms(self, symbol: str) -> float:
        """Thread-safe retrieval of last tick update latency in milliseconds."""
        with self._lock:
            entry = self._cache.get(symbol.upper())
            return entry.latency_ms if entry else 0.0

    def get_last_update_timestamp(self, symbol: str) -> Optional[datetime]:
        """Thread-safe retrieval of last update timestamp."""
        with self._lock:
            entry = self._cache.get(symbol.upper())
            return entry.last_update_timestamp if entry else None

    def get_all_latest(self) -> Dict[str, Tick]:
        """Thread-safe dictionary of all latest ticks."""
        with self._lock:
            return {sym: entry.latest_tick for sym, entry in self._cache.items() if entry.latest_tick is not None}
