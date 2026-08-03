"""Comprehensive portfolio and strategy analytics metrics."""

import math

import numpy as np
import pandas as pd


def cumulative_returns(equity: pd.Series) -> pd.Series:
    """Return cumulative return relative to first equity observation."""
    if equity.empty or equity.iloc[0] == 0:
        return pd.Series(dtype=float)
    return (equity / equity.iloc[0]) - 1.0


def calculate_max_drawdown(equity: pd.Series) -> tuple[float, float]:
    """Return (max_drawdown_amount, max_drawdown_pct)."""
    if equity.empty:
        return 0.0, 0.0

    peak = equity.cummax()
    drawdown = peak - equity
    drawdown_pct = (drawdown / peak.replace(0, np.nan)) * 100.0

    max_dd = float(drawdown.max())
    max_dd_pct = float(drawdown_pct.max()) if not pd.isna(drawdown_pct.max()) else 0.0
    return max_dd, max_dd_pct


def calculate_win_rate(pnls: list[float] | pd.Series) -> float:
    """Calculate win rate percentage."""
    if isinstance(pnls, pd.Series):
        pnls_list = pnls.dropna().tolist()
    else:
        pnls_list = [p for p in pnls if not math.isnan(p)]

    if not pnls_list:
        return 0.0

    wins = sum(1 for p in pnls_list if p > 0)
    return (wins / len(pnls_list)) * 100.0


def calculate_profit_factor(pnls: list[float] | pd.Series) -> float:
    """Calculate Profit Factor (Gross Profits / Gross Losses)."""
    if isinstance(pnls, pd.Series):
        pnls_list = pnls.dropna().tolist()
    else:
        pnls_list = [p for p in pnls if not math.isnan(p)]

    gross_profit = sum(p for p in pnls_list if p > 0)
    gross_loss = abs(sum(p for p in pnls_list if p < 0))

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def calculate_sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252
) -> float:
    """Calculate annualized Sharpe Ratio."""
    if returns.empty or len(returns) < 2:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess_returns = returns - rf_per_period
    std = float(excess_returns.std())

    if std == 0 or math.isnan(std):
        return 0.0

    mean_excess = float(excess_returns.mean())
    sharpe = (mean_excess / std) * math.sqrt(periods_per_year)
    return sharpe


def calculate_sortino_ratio(
    returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252
) -> float:
    """Calculate annualized Sortino Ratio."""
    if returns.empty or len(returns) < 2:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess_returns = returns - rf_per_period
    downside = excess_returns[excess_returns < 0]

    downside_std = float(downside.std()) if len(downside) > 1 else 0.0
    if downside_std == 0 or math.isnan(downside_std):
        return 0.0

    mean_excess = float(excess_returns.mean())
    return (mean_excess / downside_std) * math.sqrt(periods_per_year)
