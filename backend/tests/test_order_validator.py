"""Unit tests for OrderValidator."""

from decimal import Decimal

import pytest

from app.models.trading import OrderRequest, OrderType, Side
from app.paper.execution.validator import OrderValidator, OrderValidationError


def test_validator_valid_market_order():
    validator = OrderValidator()
    req = OrderRequest(symbol="AAPL", quantity=10, side=Side.BUY, order_type=OrderType.MARKET)
    validator.validate(req, available_cash=Decimal("5000.0"), current_price=Decimal("150.0"))


def test_validator_empty_symbol():
    validator = OrderValidator()
    req = OrderRequest(symbol="   ", quantity=10, side=Side.BUY)
    with pytest.raises(OrderValidationError, match="symbol cannot be empty"):
        validator.validate(req, available_cash=Decimal("5000.0"))


def test_validator_invalid_quantity():
    validator = OrderValidator()
    # Quantity <= 0 is rejected by Pydantic or validator
    req = OrderRequest(symbol="AAPL", quantity=1, side=Side.BUY)
    req.quantity = 0
    with pytest.raises(OrderValidationError, match="Invalid quantity"):
        validator.validate(req, available_cash=Decimal("5000.0"))


def test_validator_limit_order_missing_price():
    validator = OrderValidator()
    req = OrderRequest(symbol="AAPL", quantity=10, side=Side.BUY, order_type=OrderType.LIMIT, price=None)
    with pytest.raises(OrderValidationError, match="LIMIT order requires a positive price"):
        validator.validate(req, available_cash=Decimal("5000.0"))


def test_validator_insufficient_funds():
    validator = OrderValidator()
    req = OrderRequest(symbol="AAPL", quantity=100, side=Side.BUY, price=Decimal("150.0"))
    with pytest.raises(OrderValidationError, match="Insufficient funds"):
        validator.validate(req, available_cash=Decimal("1000.0"))


def test_validator_sell_order_does_not_require_buy_cash():
    validator = OrderValidator()
    req = OrderRequest(symbol="AAPL", quantity=100, side=Side.SELL, price=Decimal("150.0"))
    # Selling doesn't deduct cash balance
    validator.validate(req, available_cash=Decimal("0.0"))
