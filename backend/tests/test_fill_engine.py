"""Unit tests for FillEngine, SlippageModel, CommissionModel, and Order Types."""

from decimal import Decimal

import pytest

from app.models.trading import OrderRequest, OrderType, Side
from app.paper.execution.fill_engine import (
    CommissionModel,
    FillEngine,
    SlippageModel,
)


def test_slippage_model_buy():
    model = SlippageModel(pct=0.001, fixed_per_share=0.05)
    # 100 * 0.001 + 0.05 = 0.15 -> Fill = 100.15
    fill_price = model.calculate_fill_price(Decimal("100.0"), Side.BUY)
    assert fill_price == Decimal("100.15")


def test_slippage_model_sell():
    model = SlippageModel(pct=0.001, fixed_per_share=0.05)
    # 100 - 0.15 = 99.85
    fill_price = model.calculate_fill_price(Decimal("100.0"), Side.SELL)
    assert fill_price == Decimal("99.85")


def test_commission_model():
    model = CommissionModel(per_order=1.0, per_share=0.02, pct=0.0005)
    # 10 shares @ 100 = 1000 val. Comm = 1.0 + (0.02*10) + (1000*0.0005) = 1.0 + 0.2 + 0.5 = 1.7
    comm = model.calculate_commission(10, Decimal("100.0"))
    assert comm == Decimal("1.7")


def test_fill_engine_market_order():
    engine = FillEngine()
    req = OrderRequest(symbol="TSLA", quantity=10, side=Side.BUY, order_type=OrderType.MARKET)
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("200.0"),
        current_high=Decimal("205.0"),
        current_low=Decimal("198.0"),
        current_close=Decimal("202.0"),
    )
    assert res.filled is True
    assert res.fill_quantity == 10
    assert res.fill_price >= Decimal("200.0")


def test_fill_engine_limit_order_buy_triggered():
    engine = FillEngine()
    req = OrderRequest(
        symbol="TSLA",
        quantity=10,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("199.0"),
    )
    # Low is 198.0 <= limit 199.0 -> Triggers
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("200.0"),
        current_high=Decimal("205.0"),
        current_low=Decimal("198.0"),
        current_close=Decimal("202.0"),
    )
    assert res.filled is True
    assert res.fill_quantity == 10


def test_fill_engine_limit_order_buy_untriggered():
    engine = FillEngine()
    req = OrderRequest(
        symbol="TSLA",
        quantity=10,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("195.0"),
    )
    # Low is 198.0 > limit 195.0 -> Not triggered
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("200.0"),
        current_high=Decimal("205.0"),
        current_low=Decimal("198.0"),
        current_close=Decimal("202.0"),
    )
    assert res.filled is False


def test_fill_engine_stop_order_sell_triggered():
    engine = FillEngine()
    req = OrderRequest(
        symbol="TSLA",
        quantity=10,
        side=Side.SELL,
        order_type=OrderType.STOP_LOSS,
        price=Decimal("199.0"),
    )
    # Low is 198.0 <= stop 199.0 -> Triggers
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("200.0"),
        current_high=Decimal("205.0"),
        current_low=Decimal("198.0"),
        current_close=Decimal("202.0"),
    )
    assert res.filled is True


def test_fill_engine_partial_fill():
    engine = FillEngine(partial_fill_ratio=0.5)
    req = OrderRequest(symbol="TSLA", quantity=10, side=Side.BUY, order_type=OrderType.MARKET)
    res = engine.evaluate_fill(
        req,
        current_open=Decimal("200.0"),
        current_high=Decimal("205.0"),
        current_low=Decimal("198.0"),
        current_close=Decimal("202.0"),
    )
    assert res.filled is True
    assert res.fill_quantity == 5
    assert res.is_partial is True
