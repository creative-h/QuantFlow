"""Unit tests for OptimizationEngine grid search and random search."""

import numpy as np
import pandas as pd
import pytest

from app.research.optimization import OptimizationEngine, OptimizationResult
from app.strategies.ema_crossover import EMACrossoverStrategy


@pytest.fixture
def sample_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(50))
    open_p = close - 0.5
    high = np.maximum(open_p, close) + 1.0
    low = np.minimum(open_p, close) - 1.0
    volume = np.random.randint(1000, 5000, size=50)
    return pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def test_grid_search_sequential(sample_data: pd.DataFrame):
    engine = OptimizationEngine(initial_cash=50000.0)
    param_grid = {"fast_period": [5, 9], "slow_period": [15, 20]}

    results = engine.grid_search(
        strategy_cls=EMACrossoverStrategy,
        param_grid=param_grid,
        data=sample_data,
        top_n=3,
        max_workers=1,
    )

    assert len(results) <= 3
    assert isinstance(results[0], OptimizationResult)
    assert "fast_period" in results[0].parameters


def test_random_search(sample_data: pd.DataFrame):
    engine = OptimizationEngine(initial_cash=50000.0)
    param_dists = {"fast_period": [3, 5, 7, 9], "slow_period": [15, 20, 25, 30]}

    results = engine.random_search(
        strategy_cls=EMACrossoverStrategy,
        param_distributions=param_dists,
        n_iter=5,
        data=sample_data,
        top_n=2,
        max_workers=1,
    )

    assert len(results) <= 2
    assert isinstance(results[0], OptimizationResult)
