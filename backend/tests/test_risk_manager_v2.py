"""Unit tests for TradingRules, PositionSizer, and RiskManager."""

from decimal import Decimal

import pytest

from app.models.trading import OrderRequest, Side
from app.paper.portfolio.portfolio import ProfessionalPortfolio
from app.risk.manager import RiskManager
from app.risk.position_sizer import PositionSizer
from app.risk.rules import TradingRules


def test_position_sizer_models():
    assert PositionSizer.fixed_quantity(50) == 50
    assert PositionSizer.fixed_capital(capital_per_trade=1000.0, asset_price=50.0) == 20

    # Risk 2% of $100,000 = $2,000 risk. Entry 100, Stop 90 (risk/share = 10) -> 200 shares
    risk_qty = PositionSizer.risk_percentage(
        account_equity=100000.0, risk_pct=2.0, entry_price=100.0, stop_loss_price=90.0
    )
    assert risk_qty == 200

    # ATR volatility sizer
    atr_qty = PositionSizer.atr_volatility(
        account_equity=100000.0, risk_pct=1.0, atr_value=2.5, atr_multiplier=2.0
    )
    # Risk $1000 / (2.5 * 2 = 5) = 200 shares
    assert atr_qty == 200


def test_trading_rules_validation():
    rules = TradingRules(
        max_order_size=100, max_position_size=200, max_position_value=10000.0, max_drawdown_pct=10.0
    )

    # Valid order
    ok, _ = rules.validate_order(
        symbol="AAPL",
        quantity=50,
        price=Decimal("100.0"),
        current_position_qty=0,
        current_drawdown_pct=2.0,
    )
    assert ok is True

    # Order size too large
    ok, reason = rules.validate_order(
        symbol="AAPL",
        quantity=150,
        price=Decimal("100.0"),
        current_position_qty=0,
        current_drawdown_pct=2.0,
    )
    assert ok is False
    assert "max_order_size" in reason

    # Max drawdown exceeded
    ok, reason = rules.validate_order(
        symbol="AAPL",
        quantity=10,
        price=Decimal("100.0"),
        current_position_qty=0,
        current_drawdown_pct=15.0,
    )
    assert ok is False
    assert "drawdown" in reason.lower()


def test_risk_manager_evaluate_order():
    rm = RiskManager()
    port = ProfessionalPortfolio(initial_cash=50000.0)

    req = OrderRequest(symbol="AMZN", quantity=10, side=Side.BUY, price=Decimal("100.0"))
    approved, reason = rm.evaluate_order(req, port)
    assert approved is True
