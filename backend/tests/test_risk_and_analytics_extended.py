"""Extended unit tests for risk management models, position sizing, and analytics ratios."""

import math
from decimal import Decimal

import pandas as pd
import pytest

from app.analytics.metrics import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_win_rate,
)
from app.analytics.reports import PerformanceReport, backtest_summary
from app.backtesting.engine import BacktestResult
from app.models.trading import OrderRequest, Side
from app.paper.journal.trade_journal import TradeJournal
from app.paper.portfolio.portfolio import ProfessionalPortfolio
from app.risk.position_sizer import PositionSizer
from app.risk.rules import TradingRules


def test_position_sizer_edge_cases():
    assert PositionSizer.fixed_capital(capital_per_trade=1000.0, asset_price=0.0) == 1
    assert PositionSizer.risk_percentage(10000.0, 1.0, 100.0, 100.0) == 1
    assert PositionSizer.atr_volatility(10000.0, 1.0, 0.0) == 1


def test_trading_rules_max_position_value_breach():
    rules = TradingRules(max_position_value=5000.0)
    ok, reason = rules.validate_order(
        symbol="AAPL",
        quantity=100,
        price=Decimal("100.0"),  # $10,000 > $5,000
        current_position_qty=0,
        current_drawdown_pct=0.0,
    )
    assert ok is False
    assert "max_position_value" in reason


def test_metrics_empty_series_and_edge_cases():
    assert calculate_max_drawdown(pd.Series(dtype=float)) == (0.0, 0.0)
    assert calculate_win_rate([]) == 0.0
    assert calculate_profit_factor([]) == 0.0
    assert calculate_profit_factor([100.0, 200.0]) == float("inf")
    assert calculate_sharpe_ratio(pd.Series(dtype=float)) == 0.0
    assert calculate_sortino_ratio(pd.Series(dtype=float)) == 0.0


def test_sharpe_ratio_zero_std():
    returns = pd.Series([0.01, 0.01, 0.01, 0.01])
    assert calculate_sharpe_ratio(returns) == 0.0


def test_sortino_ratio_no_downside():
    returns = pd.Series([0.01, 0.02, 0.03, 0.015])
    assert calculate_sortino_ratio(returns) == 0.0


def test_backtest_summary_helper():
    res = BacktestResult(
        equity_curve=pd.Series([100.0, 110.0]),
        trades=[],
        net_profit=10.0,
        max_drawdown=0.0,
        win_rate=100.0,
        profit_factor=2.5,
        sharpe_ratio=1.8,
    )
    summary = backtest_summary(res)
    assert summary["net_profit"] == 10.0
    assert summary["profit_factor"] == 2.5
    assert summary["sharpe_ratio"] == 1.8


def test_portfolio_unrealized_and_realized_accumulation():
    port = ProfessionalPortfolio(initial_cash=50000.0)
    port.record_fill("1", "TSLA", Side.BUY, 10, Decimal("200.0"))
    port.update_market_price("TSLA", Decimal("210.0"))

    assert port.total_unrealized_pnl == Decimal("100.0")
    assert port.total_realized_pnl == Decimal("0.0")

    port.record_fill("2", "TSLA", Side.SELL, 5, Decimal("215.0"))
    assert port.total_realized_pnl == Decimal("75.0")
    assert port.total_unrealized_pnl == Decimal("75.0")
