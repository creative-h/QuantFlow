"""Performance statistic calculations."""

import math

import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    """Return the largest peak-to-trough drawdown as a negative fraction."""

    return float((equity / equity.cummax() - 1).min())


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Return annualised Sharpe ratio with a zero risk-free rate."""

    standard_deviation = returns.std(ddof=1)
    return 0.0 if standard_deviation == 0 or pd.isna(standard_deviation) else float(math.sqrt(periods_per_year) * returns.mean() / standard_deviation)
