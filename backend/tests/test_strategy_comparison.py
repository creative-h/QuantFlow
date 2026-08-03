"""Unit tests for StrategyComparisonEngine."""

import numpy as np
import pandas as pd
import pytest

from app.research.comparison import StrategyComparisonEngine, StrategyComparisonReport
from app.strategies.ema_crossover import EMACrossoverStrategy
from app.strategies.rsi_strategy import RSIPullbackStrategy
from app.strategies.supertrend_strategy import SupertrendStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(60))
    open_p = close - 0.5
    high = np.maximum(open_p, close) + 1.0
    low = np.minimum(open_p, close) - 1.0
    volume = np.random.randint(1000, 5000, size=60)
    return pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def test_strategy_comparison_engine(sample_data: pd.DataFrame):
    comp_engine = StrategyComparisonEngine(initial_cash=50000.0)
    strategies = [
        EMACrossoverStrategy(fast_period=5, slow_period=15),
        SupertrendStrategy(period=7, multiplier=3.0),
        RSIPullbackStrategy(period=14),
    ]

    report = comp_engine.compare(strategies, sample_data)
    assert isinstance(report, StrategyComparisonReport)
    assert len(report.items) == 3
    assert report.items[0].rank == 1

    df_comp = report.to_dataframe()
    assert isinstance(df_comp, pd.DataFrame)
    assert "strategy_name" in df_comp.columns
    assert "sharpe_ratio" in df_comp.columns
