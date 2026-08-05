"""Real-time Candle Builder converting tick streams into multi-timeframe candles (1m, 3m, 5m, 15m)."""

from datetime import datetime
from typing import Callable, Dict, List, Optional

import pandas as pd
from loguru import logger

from app.marketdata.live_feed import Tick
from app.models.dataclasses import Candle


class CandleBuilder:
    """Aggregates tick streams into 1m, 3m, 5m, and 15m candles and emits completed bars."""

    TIMEFRAMES = {
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
    }

    def __init__(self) -> None:
        self._current_candles: Dict[str, Dict[str, Dict]] = {}
        self._completed_candles: Dict[str, Dict[str, List[Candle]]] = {}
        self._listeners: List[Callable[[str, str, Candle], None]] = []

    def register_listener(self, callback: Callable[[str, str, Candle], None]) -> None:
        """Register completed candle callback: callback(symbol, timeframe, candle)."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def process_tick(self, tick: Tick) -> None:
        """Process incoming price tick and aggregate into multi-timeframe candles."""
        symbol = tick.symbol.upper()
        if symbol not in self._current_candles:
            self._current_candles[symbol] = {}
            self._completed_candles[symbol] = {tf: [] for tf in self.TIMEFRAMES}

        for tf, interval_sec in self.TIMEFRAMES.items():
            # Truncate timestamp to timeframe interval boundary
            ts_epoch = int(tick.timestamp.timestamp())
            bar_start_epoch = (ts_epoch // interval_sec) * interval_sec
            bar_timestamp = datetime.fromtimestamp(bar_start_epoch)

            current = self._current_candles[symbol].get(tf)

            if current is None or current["timestamp"] != bar_timestamp:
                # Close and emit previous bar if present
                if current is not None:
                    completed_bar = Candle(
                        timestamp=current["timestamp"],
                        open=current["open"],
                        high=current["high"],
                        low=current["low"],
                        close=current["close"],
                        volume=current["volume"],
                    )
                    self._completed_candles[symbol][tf].append(completed_bar)
                    self._emit_completed_candle(symbol, tf, completed_bar)

                # Initialize new bar
                self._current_candles[symbol][tf] = {
                    "timestamp": bar_timestamp,
                    "open": tick.price,
                    "high": tick.price,
                    "low": tick.price,
                    "close": tick.price,
                    "volume": tick.volume,
                }
            else:
                # Update ongoing bar
                current["high"] = max(current["high"], tick.price)
                current["low"] = min(current["low"], tick.price)
                current["close"] = tick.price
                current["volume"] += tick.volume

    def _emit_completed_candle(self, symbol: str, timeframe: str, candle: Candle) -> None:
        """Notify listeners of completed candle bar."""
        for listener in list(self._listeners):
            try:
                listener(symbol, timeframe, candle)
            except Exception as err:
                logger.error("Error in candle listener callback: {}", str(err))

    def get_candle_history(self, symbol: str, timeframe: str = "1m") -> List[Candle]:
        """Return history of completed candles for a symbol and timeframe."""
        symbol = symbol.upper()
        return list(self._completed_candles.get(symbol, {}).get(timeframe, []))

    def get_candle_dataframe(self, symbol: str, timeframe: str = "1m") -> pd.DataFrame:
        """Return completed candles as pandas DataFrame with OHLCV columns."""
        candles = self.get_candle_history(symbol, timeframe)
        if not candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(
            [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles
            ]
        )
        df.set_index("timestamp", inplace=True)
        return df
