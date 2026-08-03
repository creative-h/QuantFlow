"""Strategy Comparison Engine evaluating multiple strategies on identical market datasets."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import pandas as pd
from loguru import logger

from app.analytics.metrics import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_win_rate,
)
from app.backtesting.engine import BacktestEngine
from app.strategies.base import Strategy


@dataclass
class StrategyComparisonItem:
    """Performance summary of a single strategy in comparative evaluation."""

    strategy_name: str
    net_profit: float
    return_pct: float
    win_rate: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    total_trades: int
    expectancy: float
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyComparisonReport:
    """Comparative report across multiple strategy runs."""

    items: List[StrategyComparisonItem]

    def to_dataframe(self) -> pd.DataFrame:
        """Export comparative results as pandas DataFrame."""
        if not self.items:
            return pd.DataFrame()
        return pd.DataFrame([item.to_dict() for item in self.items])


class StrategyComparisonEngine:
    """Evaluates multiple quantitative strategies against identical market data."""

    def __init__(self, initial_cash: float = 100000.0) -> None:
        self.initial_cash = initial_cash

    def compare(
        self,
        strategies: List[Strategy],
        data: pd.DataFrame,
        rank_by: str = "sharpe_ratio",
    ) -> StrategyComparisonReport:
        """Run backtest for each strategy on data and compare metrics."""
        items: List[StrategyComparisonItem] = []

        for strat in strategies:
            strat_name = getattr(strat, "name", strat.__class__.__name__)
            logger.info("Evaluating strategy '{}' for comparison", strat_name)

            engine = BacktestEngine(initial_capital=self.initial_cash)
            res = engine.run(data, strat)

            net_profit = float(res.net_profit)
            ret_pct = (net_profit / self.initial_cash) * 100.0 if self.initial_cash > 0 else 0.0

            trade_frame = res.trades
            pnls = []
            if not trade_frame.empty and "quantity" in trade_frame.columns and "price" in trade_frame.columns:
                pnls_series = trade_frame["quantity"] * trade_frame["price"] * -1
                pnls = [float(p) for p in pnls_series if p != 0]

            win_rate = calculate_win_rate(pnls) if pnls else res.win_rate
            pf = calculate_profit_factor(pnls) if pnls else res.profit_factor
            _, max_dd_pct = calculate_max_drawdown(res.equity_curve)
            returns = res.equity_curve.pct_change().dropna()
            sharpe = calculate_sharpe_ratio(returns)

            wins = [p for p in pnls if p > 0]
            losses = [abs(p) for p in pnls if p < 0]
            avg_w = (sum(wins) / len(wins)) if wins else 0.0
            avg_l = (sum(losses) / len(losses)) if losses else 0.0
            p_w = (len(wins) / len(pnls)) if pnls else 0.0
            p_l = (len(losses) / len(pnls)) if pnls else 0.0
            exp = (p_w * avg_w) - (p_l * avg_l)

            item = StrategyComparisonItem(
                strategy_name=strat_name,
                net_profit=net_profit,
                return_pct=ret_pct,
                win_rate=win_rate,
                max_drawdown_pct=max_dd_pct,
                sharpe_ratio=sharpe,
                profit_factor=pf,
                total_trades=len(pnls),
                expectancy=exp,
            )
            items.append(item)

        items.sort(key=lambda x: getattr(x, rank_by, 0.0), reverse=True)
        for rank_idx, item in enumerate(items, start=1):
            item.rank = rank_idx

        return StrategyComparisonReport(items=items)
