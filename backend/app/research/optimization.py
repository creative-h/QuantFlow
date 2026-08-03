"""Parameter Optimization Engine supporting Grid Search, Random Search, and Parallel Execution."""

import importlib
import itertools
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Type

import pandas as pd
from loguru import logger

from app.analytics.metrics import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_win_rate,
)
from app.backtesting.engine import BacktestEngine
from app.strategies.base import Strategy


@dataclass
class OptimizationResult:
    """Result of a single parameter combination run."""

    parameters: Dict[str, Any]
    net_profit: float
    return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    win_rate: float
    max_drawdown_pct: float
    total_trades: int
    expectancy: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _evaluate_params(
    strategy_mod: str,
    strategy_cls_name: str,
    params: Dict[str, Any],
    df_json: str,
    initial_cash: float,
) -> OptimizationResult:
    """Top-level worker function for parallel parameter evaluation."""
    mod = importlib.import_module(strategy_mod)
    cls_ = getattr(mod, strategy_cls_name)
    strategy = cls_(**params)

    from io import StringIO

    df = pd.read_json(StringIO(df_json), orient="split")

    engine = BacktestEngine(initial_capital=initial_cash)
    run_res = engine.run(df, strategy)

    net_profit = float(run_res.net_profit)
    return_pct = (net_profit / initial_cash) * 100.0 if initial_cash > 0 else 0.0

    trade_frame = run_res.trades
    pnls = []
    if not trade_frame.empty and "quantity" in trade_frame.columns and "price" in trade_frame.columns:
        pnls_series = trade_frame["quantity"] * trade_frame["price"] * -1
        pnls = [float(p) for p in pnls_series if p != 0]

    win_rate = calculate_win_rate(pnls) if pnls else run_res.win_rate
    pf = calculate_profit_factor(pnls) if pnls else run_res.profit_factor
    _, max_dd_pct = calculate_max_drawdown(run_res.equity_curve)
    returns = run_res.equity_curve.pct_change().dropna()
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)

    wins = [p for p in pnls if p > 0]
    losses = [abs(p) for p in pnls if p < 0]
    avg_win = (sum(wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(losses) / len(losses)) if losses else 0.0
    win_prob = (len(wins) / len(pnls)) if pnls else 0.0
    loss_prob = (len(losses) / len(pnls)) if pnls else 0.0
    expectancy = (win_prob * avg_win) - (loss_prob * avg_loss)

    return OptimizationResult(
        parameters=params,
        net_profit=net_profit,
        return_pct=return_pct,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        profit_factor=pf,
        win_rate=win_rate,
        max_drawdown_pct=max_dd_pct,
        total_trades=len(pnls),
        expectancy=expectancy,
    )


class OptimizationEngine:
    """Engine executing grid search and random search parameter optimization."""

    def __init__(self, initial_cash: float = 100000.0) -> None:
        self.initial_cash = initial_cash

    def grid_search(
        self,
        strategy_cls: Type[Strategy],
        param_grid: Dict[str, List[Any]],
        data: pd.DataFrame,
        top_n: int = 10,
        sort_by: str = "sharpe_ratio",
        max_workers: Optional[int] = None,
    ) -> List[OptimizationResult]:
        """Perform grid search over parameter space."""
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = [
            dict(zip(param_names, prod)) for prod in itertools.product(*param_values)
        ]

        logger.info(
            "Starting Grid Search for {} with {} parameter combinations",
            strategy_cls.__name__,
            len(combinations),
        )
        return self._run_optimization(
            strategy_cls=strategy_cls,
            combinations=combinations,
            data=data,
            top_n=top_n,
            sort_by=sort_by,
            max_workers=max_workers,
        )

    def random_search(
        self,
        strategy_cls: Type[Strategy],
        param_distributions: Dict[str, List[Any]],
        n_iter: int = 20,
        data: pd.DataFrame = None,
        top_n: int = 10,
        sort_by: str = "sharpe_ratio",
        max_workers: Optional[int] = None,
    ) -> List[OptimizationResult]:
        """Perform random search sampling N iterations from parameter space."""
        param_names = list(param_distributions.keys())
        combinations: List[Dict[str, Any]] = []

        for _ in range(n_iter):
            combo = {name: random.choice(param_distributions[name]) for name in param_names}
            if combo not in combinations:
                combinations.append(combo)

        logger.info(
            "Starting Random Search for {} with {} sampled combinations",
            strategy_cls.__name__,
            len(combinations),
        )
        return self._run_optimization(
            strategy_cls=strategy_cls,
            combinations=combinations,
            data=data,
            top_n=top_n,
            sort_by=sort_by,
            max_workers=max_workers,
        )

    def _run_optimization(
        self,
        strategy_cls: Type[Strategy],
        combinations: List[Dict[str, Any]],
        data: pd.DataFrame,
        top_n: int,
        sort_by: str,
        max_workers: Optional[int],
    ) -> List[OptimizationResult]:
        """Execute evaluation loop sequentially or in parallel."""
        results: List[OptimizationResult] = []
        df_json = data.to_json(orient="split", date_format="iso")
        mod_name = strategy_cls.__module__
        cls_name = strategy_cls.__name__

        if max_workers == 1 or len(combinations) == 1:
            for params in combinations:
                res = _evaluate_params(mod_name, cls_name, params, df_json, self.initial_cash)
                results.append(res)
        else:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        _evaluate_params,
                        mod_name,
                        cls_name,
                        params,
                        df_json,
                        self.initial_cash,
                    )
                    for params in combinations
                ]
                for future in futures:
                    results.append(future.result())

        results.sort(key=lambda r: getattr(r, sort_by, 0.0), reverse=True)
        return results[:top_n]
