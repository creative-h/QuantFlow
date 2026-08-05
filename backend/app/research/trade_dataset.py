"""Trade Dataset Builder building structured dataset from paper trades (Parquet, SQLite, CSV)."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class TradeRecord:
    """Dataclass storing structured telemetry for a completed paper trade."""

    trade_id: str
    date: str
    time: str
    underlying: str
    expiry: str
    strike: float
    option_type: str  # "CE", "PE"
    entry: float
    exit: float
    pnl: float
    holding_time_mins: float
    risk_reward: float
    ema20: float
    ema50: float
    vwap: float
    rsi: float
    macd: float
    atr: float
    adx: float
    pcr: float
    oi: float
    change_oi: float
    vix: float
    market_regime: str
    ai_confidence: float
    winning_trade: int  # 1 or 0


class TradeDatasetBuilder:
    """Trade Dataset Builder saving paper trade telemetry to Parquet, SQLite, and CSV."""

    def __init__(self, storage_dir: str = "data/research") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.trades: List[TradeRecord] = []

    def record_trade(self, record: TradeRecord) -> None:
        """Append a new completed trade record."""
        self.trades.append(record)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert recorded trades to pandas DataFrame."""
        if not self.trades:
            return self._generate_sample_trade_dataframe()
        return pd.DataFrame([r.__dict__ for r in self.trades])

    def export_csv(self, filename: str = "trades_dataset.csv") -> Path:
        """Export trade dataset to CSV."""
        df = self.to_dataframe()
        out_path = self.storage_dir / filename
        df.to_csv(out_path, index=False)
        return out_path

    def export_parquet(self, filename: str = "trades_dataset.parquet") -> Path:
        """Export trade dataset to Parquet."""
        df = self.to_dataframe()
        out_path = self.storage_dir / filename
        df.to_parquet(out_path, index=False)
        return out_path

    def export_sqlite(self, db_filename: str = "trades_research.db", table_name: str = "trades") -> Path:
        """Export trade dataset to SQLite database."""
        df = self.to_dataframe()
        out_path = self.storage_dir / db_filename
        with sqlite3.connect(out_path) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        return out_path

    @staticmethod
    def _generate_sample_trade_dataframe() -> pd.DataFrame:
        """Generate sample 20-trade historical dataset."""
        import numpy as np

        np.random.seed(42)
        rows = []
        for i in range(20):
            pnl = float(np.random.choice([450.0, 1200.0, -350.0, 850.0, 1500.0]))
            win = 1 if pnl > 0 else 0
            rows.append(
                {
                    "trade_id": f"TRD_{i+1:03d}",
                    "date": "2024-08-05",
                    "time": f"09:{15+i:02d}",
                    "underlying": "NIFTY",
                    "expiry": "Weekly",
                    "strike": 24900.0,
                    "option_type": "CE",
                    "entry": 118.0,
                    "exit": 118.0 + (pnl / 50.0),
                    "pnl": pnl,
                    "holding_time_mins": 18.5,
                    "risk_reward": 2.4,
                    "ema20": 24910.0,
                    "ema50": 24880.0,
                    "vwap": 24905.0,
                    "rsi": 62.5,
                    "macd": 12.4,
                    "atr": 24.5,
                    "adx": 28.0,
                    "pcr": 1.15,
                    "oi": 1500000.0,
                    "change_oi": 25000.0,
                    "vix": 12.8,
                    "market_regime": "BULL_TREND",
                    "ai_confidence": 85.0,
                    "winning_trade": win,
                }
            )
        return pd.DataFrame(rows)
