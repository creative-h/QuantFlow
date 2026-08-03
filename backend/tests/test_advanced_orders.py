"""Additional unit tests for advanced order types, fill engine edge cases, slippage, and commission."""

from decimal import Decimal

import pytest

from app.models.trading import OrderRequest, OrderType, Side
from app.paper.execution.fill_engine import (
    CommissionModel,
    FillEngine,
    SlippageModel,
)
from app.paper.execution.validator import OrderValidator, OrderValidationError


def test_slippage_model_flat_only():
    model = SlippageModel(pct=0.0, fixed_per_share=0.25)
    buy_fill = model.calculate_fill_price(Decimal("100.0"), Side.BUY)
    sell_fill = model.calculate_fill_price(Decimal("100.0"), Side.SELL)
    assert buy_fill == Decimal("100.25")
    assert sell_fill == Decimal("99.75")


def test_commission_model_combined():
    model = CommissionModel(per_order=2.0, per_share=0.01, pct=0.001)
    # 100 shares @ 50.0 = 5000 value.
    # Commission = 2.0 + (0.01 * 100) + (5000 * 0.001) = 2.0 + 1.0 + 5.0 = 8.0
    comm = model.calculate_commission(100, Decimal("50.0"))
    assert comm == Decimal("8.0")


def test_limit_order_sell_untriggered():
    engine = FillEngine()
    req = OrderRequest(
        symbol="MSFT",
        quantity=10,
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("350.0"),
    )
    # High is 345.0 < 350.0 -> Untriggered
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("340.0"),
        current_high=Decimal("345.0"),
        current_low=Decimal("338.0"),
        current_close=Decimal("342.0"),
    )
    assert res.filled is False


def test_stop_order_buy_untriggered():
    engine = FillEngine()
    req = OrderRequest(
        symbol="MSFT",
        quantity=10,
        side=Side.BUY,
        order_type=OrderType.STOP_LOSS,
        price=Decimal("360.0"),
    )
    # High is 355.0 < stop 360.0 -> Untriggered
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("350.0"),
        current_high=Decimal("355.0"),
        current_low=Decimal("348.0"),
        current_close=Decimal("352.0"),
    )
    assert res.filled is False


def test_fill_engine_zero_remaining_quantity():
    engine = FillEngine()
    req = OrderRequest(symbol="MSFT", quantity=10, side=Side.BUY)
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("300.0"),
        current_high=Decimal("305.0"),
        current_low=Decimal("298.0"),
        current_close=Decimal("302.0"),
        already_filled_qty=10,
    )
    assert res.filled is False
    assert res.fill_quantity == 0


def test_order_validator_negative_price():
    validator = OrderValidator()
    req = OrderRequest(symbol="AAPL", quantity=10, side=Side.BUY, order_type=OrderType.LIMIT)
    req.price = Decimal("-10.0")
    with pytest.raises(OrderValidationError, match="LIMIT order requires a positive price"):
        validator.validate(req, available_cash=Decimal("1000.0"))


def test_order_validator_short_selling_allowed():
    validator = OrderValidator(allow_shorting=True)
    req = OrderRequest(symbol="AAPL", quantity=50, side=Side.SELL)
    validator.validate(req, available_cash=Decimal("0.0"))
