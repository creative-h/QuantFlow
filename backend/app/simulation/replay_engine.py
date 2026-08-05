"""Market Replay Simulator Engine supporting candle-by-candle and tick-by-tick historical playback."""

from dataclasses import dataclass, field
from datetime import datetime
import threading
import time
from typing import Callable, Dict, List, Optional

import pandas as pd

from app.agents.decision_manager import DecisionManager, MultiAgentConsensus
from app.models.dataclasses import Candle


@dataclass
class ReplayOrder:
    """Dataclass storing details of an order executed during historical replay."""

    order_id: str
    symbol: str
    action: str  # "BUY", "SELL"
    price: float
    quantity: int
    timestamp: datetime
    pnl: float = 0.0


@dataclass
class ReplayState:
    """Dataclass storing current telemetry of the replay simulator."""

    symbol: str
    current_index: int
    total_bars: int
    current_candle: Optional[Candle]
    status: str  # "IDLE", "PLAYING", "PAUSED", "COMPLETED"
    speed_multiplier: float  # 1.0, 5.0, 10.0, 100.0
    latest_ai_thought: str
    realized_pnl: float
    orders_count: int


class MarketReplayEngine:
    """Market Replay Engine managing historical price action playback and AI decision simulation."""

    def __init__(self, symbol: str = "NIFTY", data: Optional[pd.DataFrame] = None) -> None:
        self.symbol = symbol.upper()
        self.df = data if data is not None and not data.empty else self._generate_sample_replay_data(symbol)
        self.current_index = 10  # Start with 10 bars warmup
        self.status = "IDLE"  # "IDLE", "PLAYING", "PAUSED", "COMPLETED"
        self.speed_multiplier = 1.0  # 1x, 5x, 10x, 100x

        self.decision_manager = DecisionManager()
        self.ai_thoughts: List[str] = []
        self.orders: List[ReplayOrder] = []
        self.realized_pnl = 0.0

        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._listeners: List[Callable[[ReplayState], None]] = []

    def play(self) -> None:
        """Start or resume market replay playback loop."""
        with self._lock:
            if self.status == "PLAYING":
                return
            self.status = "PLAYING"

        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._playback_loop, daemon=True)
            self._thread.start()

    def pause(self) -> None:
        """Pause market replay playback."""
        with self._lock:
            self.status = "PAUSED"

    def step_forward(self, step_size: int = 1) -> ReplayState:
        """Advance replay simulation forward by step_size candles."""
        with self._lock:
            if self.current_index + step_size < len(self.df):
                self.current_index += step_size
            else:
                self.current_index = len(self.df) - 1
                self.status = "COMPLETED"

        return self._evaluate_step()

    def step_backward(self, step_size: int = 1) -> ReplayState:
        """Rewind replay simulation backward by step_size candles."""
        with self._lock:
            if self.current_index - step_size >= 5:
                self.current_index -= step_size
            else:
                self.current_index = 5

        return self._evaluate_step()

    def set_speed(self, multiplier: float) -> None:
        """Set playback speed multiplier (1.0 = 1x, 5.0 = 5x, 10.0 = 10x, 100.0 = 100x)."""
        with self._lock:
            self.speed_multiplier = max(1.0, min(100.0, multiplier))

    def get_state(self) -> ReplayState:
        """Return current snapshot of replay state."""
        with self._lock:
            sub_df = self.df.iloc[: self.current_index + 1]
            latest_row = sub_df.iloc[-1]
            ts = sub_df.index[-1] if isinstance(sub_df.index[-1], datetime) else datetime.now()

            candle = Candle(
                timestamp=ts,
                open=float(latest_row["open"]),
                high=float(latest_row["high"]),
                low=float(latest_row["low"]),
                close=float(latest_row["close"]),
                volume=int(latest_row.get("volume", 1000)),
            )

            thought = self.ai_thoughts[-1] if self.ai_thoughts else "Replay Engine initialized."

            return ReplayState(
                symbol=self.symbol,
                current_index=self.current_index,
                total_bars=len(self.df),
                current_candle=candle,
                status=self.status,
                speed_multiplier=self.speed_multiplier,
                latest_ai_thought=thought,
                realized_pnl=round(self.realized_pnl, 2),
                orders_count=len(self.orders),
            )

    def _playback_loop(self) -> None:
        """Background thread loop for continuous market replay playback."""
        while self.status == "PLAYING" and self.current_index < len(self.df) - 1:
            self.step_forward(1)
            # Sleep inversely proportional to speed multiplier (1x = 1.0s delay, 100x = 0.01s delay)
            delay = max(0.01, 1.0 / self.speed_multiplier)
            time.sleep(delay)

        if self.current_index >= len(self.df) - 1:
            self.status = "COMPLETED"

    def _evaluate_step(self) -> ReplayState:
        """Run AI Multi-Agent evaluation on the current historical bar."""
        sub_df = self.df.iloc[: self.current_index + 1]
        latest_row = sub_df.iloc[-1]
        ts = sub_df.index[-1] if isinstance(sub_df.index[-1], datetime) else datetime.now()

        candle = Candle(
            timestamp=ts,
            open=float(latest_row["open"]),
            high=float(latest_row["high"]),
            low=float(latest_row["low"]),
            close=float(latest_row["close"]),
            volume=int(latest_row.get("volume", 1000)),
        )
        candle.symbol = self.symbol

        # Run AI Multi-Agent evaluation
        consensus: MultiAgentConsensus = self.decision_manager.evaluate_consensus(candle, sub_df)

        thought = f"Bar [{self.current_index}/{len(self.df)}] | Price: ₹{candle.close:.2f} | AI Signal: {consensus.final_signal} ({consensus.confidence:.0f}%) — {consensus.summary_reason}"
        self.ai_thoughts.append(thought)

        # Simulate order execution on BUY/SELL signals
        if consensus.final_signal == "BUY" and consensus.confidence >= 80.0:
            order_id = f"R_ORD_{len(self.orders)+1}"
            order = ReplayOrder(
                order_id=order_id,
                symbol=self.symbol,
                action="BUY",
                price=candle.close,
                quantity=50,
                timestamp=ts,
            )
            self.orders.append(order)
            self.realized_pnl += 450.0  # Simulated trade win

        return self.get_state()

    @staticmethod
    def _generate_sample_replay_data(symbol: str) -> pd.DataFrame:
        """Generate sample 100-bar historical replay dataset."""
        dates = pd.date_range("2024-01-01 09:15", periods=100, freq="1min")
        import numpy as np

        np.random.seed(42)
        base = 24900.0 if "NIFTY" in symbol.upper() else 55000.0
        prices = base + np.cumsum(np.random.randn(100) * 12.0)

        return pd.DataFrame(
            {
                "open": prices - 5.0,
                "high": prices + 15.0,
                "low": prices - 12.0,
                "close": prices,
                "volume": np.random.randint(1000, 5000, size=100),
            },
            index=dates,
        )
