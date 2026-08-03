"""Serialisable reporting helpers and PerformanceReport generator."""

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from app.analytics.metrics import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_win_rate,
)
from app.backtesting.engine import BacktestResult
from app.paper.portfolio.portfolio import ProfessionalPortfolio


@dataclass
class PerformanceReport:
    """Comprehensive portfolio performance summary."""

    total_equity: float
    initial_cash: float
    net_profit: float
    return_pct: float
    realized_pnl: float
    unrealized_pnl: float
    max_drawdown: float
    max_drawdown_pct: float
    total_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float

    @classmethod
    def generate(cls, portfolio: ProfessionalPortfolio) -> "PerformanceReport":
        """Generate performance report from a ProfessionalPortfolio instance."""
        equity_series = (
            pd.Series([float(eq) for _, eq in portfolio.equity_curve])
            if portfolio.equity_curve
            else pd.Series([float(portfolio.total_equity)])
        )
        returns = equity_series.pct_change().dropna()

        pnls = [float(t.realized_pnl) for t in portfolio.trades if t.realized_pnl != 0]

        net_profit = float(portfolio.total_equity - portfolio.initial_cash)
        return_pct = (
            (net_profit / float(portfolio.initial_cash)) * 100.0
            if portfolio.initial_cash > 0
            else 0.0
        )

        max_dd, max_dd_pct = calculate_max_drawdown(equity_series)
        win_rate = calculate_win_rate(pnls)
        profit_factor = calculate_profit_factor(pnls)
        sharpe = calculate_sharpe_ratio(returns)
        sortino = calculate_sortino_ratio(returns)

        return cls(
            total_equity=float(portfolio.total_equity),
            initial_cash=float(portfolio.initial_cash),
            net_profit=net_profit,
            return_pct=return_pct,
            realized_pnl=float(portfolio.total_realized_pnl),
            unrealized_pnl=float(portfolio.total_unrealized_pnl),
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            total_trades=len(portfolio.trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return asdict(self)


def backtest_summary(result: BacktestResult) -> dict[str, float]:
    """Convert a backtest result into API-friendly scalar metrics."""
    return {
        "net_profit": result.net_profit,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "profit_factor": result.profit_factor,
        "sharpe_ratio": result.sharpe_ratio,
    }
