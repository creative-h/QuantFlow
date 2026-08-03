"""Release v0.2 comprehensive integration and unit test suite."""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest
from pydantic import ValidationError

from app.analytics.metrics import calculate_max_drawdown, calculate_win_rate
from app.analytics.reports import PerformanceReport
from app.models.trading import OrderRequest, OrderStatus, OrderType, Side
from app.paper.execution.execution_engine import ExecutionEngine
from app.paper.execution.fill_engine import CommissionModel, FillEngine, SlippageModel
from app.paper.execution.validator import OrderValidator, OrderValidationError
from app.paper.journal.trade_journal import TradeJournal
from app.paper.portfolio.portfolio import ProfessionalPortfolio
from app.risk.position_sizer import PositionSizer
from app.risk.rules import TradingRules


def test_suite_market_order_fill_with_slippage_and_commission():
    engine = FillEngine(
        slippage_model=SlippageModel(pct=0.001),
        commission_model=CommissionModel(per_order=1.0, pct=0.0005),
    )
    req = OrderRequest(symbol="INFY", quantity=20, side=Side.BUY, order_type=OrderType.MARKET)
    res = engine.evaluate_fill(
        req, Decimal("1500.0"), Decimal("1510.0"), Decimal("1490.0"), Decimal("1505.0")
    )
    assert res.filled is True
    assert res.fill_price == Decimal("1501.5")
    assert res.commission > Decimal("0")


def test_suite_limit_order_buy_fill():
    engine = FillEngine()
    req = OrderRequest(
        symbol="INFY",
        quantity=10,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("1495.0"),
    )
    res = engine.evaluate_fill(
        req, Decimal("1500.0"), Decimal("1510.0"), Decimal("1490.0"), Decimal("1505.0")
    )
    assert res.filled is True


def test_suite_limit_order_sell_fill():
    engine = FillEngine()
    req = OrderRequest(
        symbol="INFY",
        quantity=10,
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("1508.0"),
    )
    res = engine.evaluate_fill(
        req, Decimal("1500.0"), Decimal("1510.0"), Decimal("1490.0"), Decimal("1505.0")
    )
    assert res.filled is True


def test_suite_stop_order_buy_trigger():
    engine = FillEngine()
    req = OrderRequest(
        symbol="INFY",
        quantity=10,
        side=Side.BUY,
        order_type=OrderType.STOP_LOSS,
        price=Decimal("1505.0"),
    )
    res = engine.evaluate_fill(
        req, Decimal("1500.0"), Decimal("1510.0"), Decimal("1490.0"), Decimal("1505.0")
    )
    assert res.filled is True


def test_suite_stop_order_sell_trigger():
    engine = FillEngine()
    req = OrderRequest(
        symbol="INFY",
        quantity=10,
        side=Side.SELL,
        order_type=OrderType.STOP_LOSS,
        price=Decimal("1495.0"),
    )
    res = engine.evaluate_fill(
        req, Decimal("1500.0"), Decimal("1510.0"), Decimal("1490.0"), Decimal("1505.0")
    )
    assert res.filled is True


def test_suite_partial_fill_calculation():
    engine = FillEngine(partial_fill_ratio=0.4)
    req = OrderRequest(symbol="INFY", quantity=25, side=Side.BUY)
    res = engine.evaluate_fill(
        req, Decimal("1500.0"), Decimal("1510.0"), Decimal("1490.0"), Decimal("1505.0")
    )
    assert res.fill_quantity == 10
    assert res.is_partial is True


def test_suite_validator_rejects_empty_symbol():
    with pytest.raises((ValidationError, OrderValidationError)):
        req = OrderRequest(symbol="", quantity=10, side=Side.BUY)
        validator = OrderValidator()
        validator.validate(req, Decimal("10000.0"))


def test_suite_validator_rejects_zero_quantity():
    validator = OrderValidator()
    req = OrderRequest(symbol="SBIN", quantity=1, side=Side.BUY)
    req.quantity = 0
    with pytest.raises(OrderValidationError):
        validator.validate(req, Decimal("10000.0"))


def test_suite_validator_rejects_limit_without_price():
    validator = OrderValidator()
    req = OrderRequest(symbol="SBIN", quantity=10, side=Side.BUY, order_type=OrderType.LIMIT)
    with pytest.raises(OrderValidationError):
        validator.validate(req, Decimal("10000.0"))


def test_suite_validator_rejects_insufficient_cash():
    validator = OrderValidator()
    req = OrderRequest(symbol="SBIN", quantity=100, side=Side.BUY, price=Decimal("600.0"))
    with pytest.raises(OrderValidationError):
        validator.validate(req, Decimal("5000.0"))


def test_suite_trading_rules_order_size_limit():
    rules = TradingRules(max_order_size=50)
    ok, _ = rules.validate_order("SBIN", 30, Decimal("600.0"), 0, 0.0)
    assert ok is True
    ok_fail, _ = rules.validate_order("SBIN", 60, Decimal("600.0"), 0, 0.0)
    assert ok_fail is False


def test_suite_trading_rules_drawdown_limit():
    rules = TradingRules(max_drawdown_pct=15.0)
    ok, _ = rules.validate_order("SBIN", 10, Decimal("600.0"), 0, 18.0)
    assert ok is False


def test_suite_position_average_price_on_multiple_buys():
    port = ProfessionalPortfolio(100000.0)
    port.record_fill("1", "SBIN", Side.BUY, 100, Decimal("500.0"))
    port.record_fill("2", "SBIN", Side.BUY, 100, Decimal("600.0"))
    pos = port.positions["SBIN"]
    assert pos.quantity == 200
    assert pos.average_price == Decimal("550.0")


def test_suite_position_realized_pnl_on_partial_sell():
    port = ProfessionalPortfolio(100000.0)
    port.record_fill("1", "SBIN", Side.BUY, 100, Decimal("500.0"))
    port.record_fill("2", "SBIN", Side.SELL, 50, Decimal("600.0"))
    pos = port.positions["SBIN"]
    assert pos.quantity == 50
    assert pos.realized_pnl == Decimal("5000.0")


def test_suite_portfolio_equity_and_peak():
    port = ProfessionalPortfolio(50000.0)
    assert port.total_equity == Decimal("50000.0")
    port.update_market_price("SBIN", Decimal("600.0"))
    assert port.peak_equity == Decimal("50000.0")


def test_suite_trade_journal_snapshot_and_dataframe():
    journal = TradeJournal()
    journal.record_snapshot(datetime.now(), Decimal("50000.0"), Decimal("40000.0"), Decimal("0.0"))
    assert len(journal.equity_snapshots) == 1
    df = journal.to_dataframe()
    assert isinstance(df, pd.DataFrame)


def test_suite_performance_report_metrics():
    port = ProfessionalPortfolio(100000.0)
    port.record_fill("1", "WIPRO", Side.BUY, 100, Decimal("400.0"))
    port.update_market_price("WIPRO", Decimal("450.0"))
    port.record_fill("2", "WIPRO", Side.SELL, 100, Decimal("450.0"))

    report = PerformanceReport.generate(port)
    assert report.total_equity == 105000.0
    assert report.net_profit == 5000.0
    assert report.win_rate == 100.0


def test_suite_position_sizer_fixed_and_volatility():
    qty_fixed = PositionSizer.fixed_quantity(75)
    assert qty_fixed == 75

    qty_cap = PositionSizer.fixed_capital(10000.0, 250.0)
    assert qty_cap == 40


def test_suite_execution_engine_order_lifecycle():
    ee = ExecutionEngine()
    req = OrderRequest(symbol="WIPRO", quantity=10, side=Side.BUY)
    order = ee.submit_order(req, Decimal("50000.0"), Decimal("400.0"))
    assert order.status == OrderStatus.OPEN

    fills = ee.process_tick("WIPRO", Decimal("400.0"), Decimal("405.0"), Decimal("395.0"), Decimal("402.0"))
    assert len(fills) == 1
    assert fills[0][0].status == OrderStatus.FILLED


def test_suite_max_drawdown_calculation():
    series = pd.Series([100.0, 110.0, 105.0, 95.0, 115.0])
    dd, dd_pct = calculate_max_drawdown(series)
    assert pytest.approx(dd) == 15.0
    assert pytest.approx(dd_pct, rel=1e-2) == 13.636


def test_suite_win_rate_calculation():
    pnls = [500.0, -200.0, 300.0, -100.0]
    wr = calculate_win_rate(pnls)
    assert wr == 50.0
