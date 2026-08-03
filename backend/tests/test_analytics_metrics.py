"""Unit tests for analytics metrics and PerformanceReport."""

from decimal import Decimal

import pandas as pd
import pytest

from app.analytics.metrics import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_win_rate,
    cumulative_returns,
)
from app.analytics.reports import PerformanceReport
from app.models.trading import Side
from app.paper.portfolio.portfolio import ProfessionalPortfolio


def test_cumulative_returns():
    equity = pd.Series([100.0, 105.0, 110.0, 108.0])
    returns = cumulative_returns(equity)
    assert pytest.approx(returns.iloc[0]) == 0.0
    assert pytest.approx(returns.iloc[2]) == 0.10


def test_calculate_max_drawdown():
    equity = pd.Series([100.0, 120.0, 90.0, 110.0])
    max_dd, max_dd_pct = calculate_max_drawdown(equity)
    # Peak is 120.0, drops to 90.0 -> DD = 30.0 (25%)
    assert max_dd == 30.0
    assert max_dd_pct == 25.0


def test_win_rate_and_profit_factor():
    pnls = [100.0, -50.0, 200.0, -50.0, 150.0]
    wr = calculate_win_rate(pnls)
    pf = calculate_profit_factor(pnls)

    # 3 wins out of 5 trades = 60%
    assert wr == 60.0
    # Gross profit = 450, Gross loss = 100 -> PF = 4.5
    assert pf == 4.5


def test_sharpe_and_sortino_ratios():
    returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.03, -0.01])
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)

    assert sharpe > 0
    assert sortino > 0


def test_performance_report_generate():
    port = ProfessionalPortfolio(initial_cash=100000.0)
    # Buy & sell trade with profit: 10 * (220 - 200) = 200 net profit
    port.record_fill(
        order_id="1", symbol="META", side=Side.BUY, quantity=10, fill_price=Decimal("200.0")
    )
    port.update_market_price("META", Decimal("220.0"))
    port.record_fill(
        order_id="2", symbol="META", side=Side.SELL, quantity=10, fill_price=Decimal("220.0")
    )

    report = PerformanceReport.generate(port)
    assert report.total_equity == 100200.0
    assert report.net_profit == 200.0
    assert pytest.approx(report.return_pct) == 0.2
    assert report.win_rate == 100.0
    assert report.total_trades == 2
    assert "net_profit" in report.to_dict()
