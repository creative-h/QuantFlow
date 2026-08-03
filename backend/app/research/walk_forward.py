"""Walk-Forward Optimization and Out-of-Sample Testing Engine."""

from dataclasses import dataclass
from typing import Any, Dict, List, Type

import pandas as pd
from loguru import logger

from app.analytics.metrics import calculate_max_drawdown, calculate_sharpe_ratio, calculate_win_rate
from app.backtesting.engine import BacktestEngine
from app.research.optimization import OptimizationEngine
from app.strategies.base import Strategy


@dataclass
class WalkForwardWindowResult:
    """Results for a single Walk-Forward train/test window."""

    window_index: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    best_params: Dict[str, Any]
    in_sample_sharpe: float
    out_sample_net_profit: float
    out_sample_sharpe: float
    out_sample_win_rate: float
    out_sample_max_dd: float


@dataclass
class WalkForwardResult:
    """Consolidated out-of-sample walk forward results."""

    strategy_name: str
    windows: List[WalkForwardWindowResult]
    consolidated_net_profit: float
    consolidated_sharpe: float
    consolidated_win_rate: float
    consolidated_max_drawdown: float
    total_out_sample_trades: int


class WalkForwardEngine:
    """Walk-Forward Testing Engine splitting data into rolling train/test segments."""

    def __init__(
        self,
        train_bars: int = 100,
        test_bars: int = 30,
        step_bars: int = 30,
        initial_cash: float = 100000.0,
    ) -> None:
        self.train_bars = train_bars
        self.test_bars = test_bars
        self.step_bars = step_bars
        self.initial_cash = initial_cash

    def run(
        self,
        strategy_cls: Type[Strategy],
        param_grid: Dict[str, List[Any]],
        data: pd.DataFrame,
    ) -> WalkForwardResult:
        """Run Walk-Forward optimization across rolling windows."""
        total_bars = len(data)
        min_required = self.train_bars + self.test_bars

        if total_bars < min_required:
            raise ValueError(
                f"Insufficient data for Walk Forward (has {total_bars} bars, requires >= {min_required})"
            )

        windows: List[WalkForwardWindowResult] = []
        all_out_sample_trades: int = 0

        start_idx = 0
        window_idx = 0

        opt_engine = OptimizationEngine(initial_cash=self.initial_cash)

        while start_idx + self.train_bars + self.test_bars <= total_bars:
            train_data = data.iloc[start_idx : start_idx + self.train_bars]
            test_data = data.iloc[
                start_idx + self.train_bars : start_idx + self.train_bars + self.test_bars
            ]

            train_start_str = str(train_data.index[0])
            train_end_str = str(train_data.index[-1])
            test_start_str = str(test_data.index[0])
            test_end_str = str(test_data.index[-1])

            logger.info(
                "WF Window {}: Train [{} - {}], Test [{} - {}]",
                window_idx,
                train_start_str,
                train_end_str,
                test_start_str,
                test_end_str,
            )

            # 1. Optimize on Train window
            top_results = opt_engine.grid_search(
                strategy_cls=strategy_cls,
                param_grid=param_grid,
                data=train_data,
                top_n=1,
                sort_by="sharpe_ratio",
                max_workers=1,
            )

            best_params = top_results[0].parameters if top_results else {}
            in_sample_sharpe = top_results[0].sharpe_ratio if top_results else 0.0

            # 2. Evaluate out-of-sample on Test window
            strategy_inst = strategy_cls(**best_params)
            bt_engine = BacktestEngine(initial_capital=self.initial_cash)
            out_res = bt_engine.run(test_data, strategy_inst)

            out_net_profit = float(out_res.net_profit)
            out_returns = out_res.equity_curve.pct_change().dropna()
            out_sharpe = calculate_sharpe_ratio(out_returns)

            trade_frame = out_res.trades
            pnls = []
            if not trade_frame.empty and "quantity" in trade_frame.columns and "price" in trade_frame.columns:
                pnls_series = trade_frame["quantity"] * trade_frame["price"] * -1
                pnls = [float(p) for p in pnls_series if p != 0]

            out_win_rate = calculate_win_rate(pnls) if pnls else out_res.win_rate
            _, max_dd_pct = calculate_max_drawdown(out_res.equity_curve)

            win_res = WalkForwardWindowResult(
                window_index=window_idx,
                train_start=train_start_str,
                train_end=train_end_str,
                test_start=test_start_str,
                test_end=test_end_str,
                best_params=best_params,
                in_sample_sharpe=in_sample_sharpe,
                out_sample_net_profit=out_net_profit,
                out_sample_sharpe=out_sharpe,
                out_sample_win_rate=out_win_rate,
                out_sample_max_dd=max_dd_pct,
            )
            windows.append(win_res)
            all_out_sample_trades += len(pnls)

            start_idx += self.step_bars
            window_idx += 1

        total_out_profit = sum(w.out_sample_net_profit for w in windows)
        avg_out_sharpe = (sum(w.out_sample_sharpe for w in windows) / len(windows)) if windows else 0.0
        avg_out_win_rate = (sum(w.out_sample_win_rate for w in windows) / len(windows)) if windows else 0.0
        max_out_dd = max((w.out_sample_max_dd for w in windows), default=0.0)

        return WalkForwardResult(
            strategy_name=getattr(strategy_cls, "name", strategy_cls.__name__),
            windows=windows,
            consolidated_net_profit=total_out_profit,
            consolidated_sharpe=avg_out_sharpe,
            consolidated_win_rate=avg_out_win_rate,
            consolidated_max_drawdown=max_out_dd,
            total_out_sample_trades=all_out_sample_trades,
        )
