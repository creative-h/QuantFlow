"""Unit tests for WalkForwardEngine."""

import numpy as np
import pandas as pd
import pytest

from app.research.walk_forward import WalkForwardEngine, WalkForwardResult
from app.strategies.ema_crossover import EMACrossoverStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(150))
    open_p = close - 0.5
    high = np.maximum(open_p, close) + 1.0
    low = np.minimum(open_p, close) - 1.0
    volume = np.random.randint(1000, 5000, size=150)
    return pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def test_walk_forward_engine_run(sample_data: pd.DataFrame):
    wf = WalkForwardEngine(train_bars=60, test_bars=30, step_bars=30)
    param_grid = {"fast_period": [5, 9], "slow_period": [15, 20]}

    result = wf.run(EMACrossoverStrategy, param_grid, sample_data)
    assert isinstance(result, WalkForwardResult)
    assert len(result.windows) >= 2
    assert result.strategy_name in ("ema", "EMACrossoverStrategy")


def test_walk_forward_insufficient_data():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    df_small = pd.DataFrame(
        {
            "open": [10.0] * 30,
            "high": [11.0] * 30,
            "low": [9.0] * 30,
            "close": [10.0] * 30,
            "volume": [100] * 30,
        },
        index=dates,
    )
    wf = WalkForwardEngine(train_bars=50, test_bars=20)
    with pytest.raises(ValueError, match="Insufficient data"):
        wf.run(EMACrossoverStrategy, {"fast_period": [5]}, df_small)
