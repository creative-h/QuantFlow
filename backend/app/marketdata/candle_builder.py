"""Multi-Timeframe Candle Builder supporting 1m, 3m, 5m, 15m, 30m, 1h, and daily bars with VWAP & OI."""

from datetime import datetime, timedelta
import threading
from typing import Callable, Dict, List, Optional

import pandas as pd

from app.marketdata.live_feed import Tick
from app.models.dataclasses import Candle


class CandleBuilder:
    """Aggregates streaming ticks into multi-timeframe candles (1m, 3m, 5m, 15m, 30m, 1h, 1d) with VWAP & OI."""

    TIMEFRAME_MINUTES = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "1d": 1440,
    }

    def __init__(self, timeframes: Optional[List[str]] = None) -> None:
        self.timeframes = timeframes or ["1m", "3m", "5m", "15m", "30m", "1h", "1d"]
        self._lock = threading.Lock()
        self._listeners: List[Callable[[str, str, Candle], None]] = []

        # Active & current bar tracking
        self._active_bars: Dict[str, Dict[str, Dict]] = {}
        self._current_candles: Dict[str, Dict[str, Dict]] = self._active_bars

        # Completed historical candles: symbol -> timeframe -> List[Candle]
        self._completed_candles: Dict[str, Dict[str, List[Candle]]] = {}

    def register_listener(self, callback: Callable[[str, str, Candle], None]) -> None:
        """Register callback for completed candle emissions."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def process_tick(self, tick: Tick) -> None:
        """Process incoming tick, updating active candles across all timeframes."""
        sym = tick.symbol.upper()
        now = tick.timestamp or datetime.now()

        with self._lock:
            if sym not in self._active_bars:
                self._active_bars[sym] = {}
                self._completed_candles[sym] = {tf: [] for tf in self.timeframes}

            for tf in self.timeframes:
                interval_min = self.TIMEFRAME_MINUTES.get(tf, 1)
                bar_start = self._calculate_bar_start(now, interval_min)

                active = self._active_bars[sym].get(tf)

                if active is None or active["start_time"] != bar_start:
                    # Emit completed bar if previous exists
                    if active is not None:
                        vwap_val = round(active["typical_vol_sum"] / active["volume"], 2) if active["volume"] > 0 else active["close"]
                        completed_bar = Candle(
                            timestamp=active["start_time"],
                            open=active["open"],
                            high=active["high"],
                            low=active["low"],
                            close=active["close"],
                            volume=active["volume"],
                        )
                        completed_bar.vwap = vwap_val
                        completed_bar.oi = active["oi"]

                        self._completed_candles[sym][tf].append(completed_bar)

                        # Trigger listeners
                        for cb in self._listeners:
                            try:
                                cb(sym, tf, completed_bar)
                            except Exception:
                                pass

                    # Initialize new bar
                    self._active_bars[sym][tf] = {
                        "start_time": bar_start,
                        "open": tick.price,
                        "high": tick.price,
                        "low": tick.price,
                        "close": tick.price,
                        "volume": tick.volume,
                        "oi": tick.oi,
                        "typical_vol_sum": tick.price * max(1, tick.volume),
                        "timestamp": bar_start,
                    }
                else:
                    # Update active bar
                    active["high"] = max(active["high"], tick.price)
                    active["low"] = min(active["low"], tick.price)
                    active["close"] = tick.price
                    active["volume"] += tick.volume
                    active["oi"] = tick.oi
                    active["typical_vol_sum"] += tick.price * max(1, tick.volume)

    def get_completed_candles(self, symbol: str, timeframe: str = "1m") -> List[Candle]:
        """Return thread-safe list of completed candles for a symbol and timeframe."""
        with self._lock:
            sym_dict = self._completed_candles.get(symbol.upper())
            if sym_dict and timeframe in sym_dict:
                return list(sym_dict[timeframe])
            return []

    def get_candle_dataframe(self, symbol: str, timeframe: str = "1m") -> pd.DataFrame:
        """Convert completed candles for a symbol into a pandas DataFrame."""
        candles = self.get_completed_candles(symbol, timeframe)
        if not candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        rows = []
        for c in candles:
            rows.append(
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
            )
        df = pd.DataFrame(rows)
        df.set_index("timestamp", inplace=True)
        return df

    def _calculate_bar_start(self, dt: datetime, interval_min: int) -> datetime:
        """Calculate floored bar start timestamp for given interval."""
        if interval_min == 1440:
            return dt.replace(hour=9, minute=15, second=0, microsecond=0)
        total_minutes = dt.hour * 60 + dt.minute
        floored_minutes = (total_minutes // interval_min) * interval_min
        hour = floored_minutes // 60
        minute = floored_minutes % 60
        return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
