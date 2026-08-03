"""Unit tests for ExecutionEngine and OrderManager."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.trading import Order, OrderRequest, OrderStatus, Side
from app.paper.execution.execution_engine import ExecutionEngine
from app.paper.execution.order_manager import OrderManager


def test_order_manager_operations():
    om = OrderManager()
    req = OrderRequest(symbol="MSFT", quantity=5, side=Side.BUY)

    order = Order(
        id=str(uuid4()),
        request=req,
        status=OrderStatus.OPEN,
        filled_quantity=0,
        average_price=None,
        created_at=datetime.now(UTC),
    )
    om.add_order(order)
    assert om.get_order(order.id) == order
    assert len(om.list_orders(status=OrderStatus.OPEN)) == 1
    assert len(om.list_orders(symbol="MSFT")) == 1


def test_execution_engine_submit_and_process():
    ee = ExecutionEngine(latency_ticks=0)
    req = OrderRequest(symbol="MSFT", quantity=10, side=Side.BUY)
    order = ee.submit_order(req, available_cash=Decimal("10000.0"), current_price=Decimal("300.0"))

    assert order.status == OrderStatus.OPEN

    fills = ee.process_tick(
        symbol="MSFT",
        open_price=Decimal("300.0"),
        high_price=Decimal("305.0"),
        low_price=Decimal("298.0"),
        close_price=Decimal("302.0"),
    )

    assert len(fills) == 1
    filled_order, fill_res = fills[0]
    assert filled_order.status == OrderStatus.FILLED
    assert fill_res.fill_quantity == 10


def test_execution_engine_simulated_latency():
    ee = ExecutionEngine(latency_ticks=3)
    req = OrderRequest(symbol="MSFT", quantity=10, side=Side.BUY)
    order = ee.submit_order(req, available_cash=Decimal("10000.0"), current_price=Decimal("300.0"))

    # Tick 1: Latency delay -> No fill
    fills_t1 = ee.process_tick(
        "MSFT", Decimal("300.0"), Decimal("305.0"), Decimal("298.0"), Decimal("302.0")
    )
    assert len(fills_t1) == 0

    # Tick 2: Latency delay -> No fill
    fills_t2 = ee.process_tick(
        "MSFT", Decimal("300.0"), Decimal("305.0"), Decimal("298.0"), Decimal("302.0")
    )
    assert len(fills_t2) == 0

    # Tick 3: Latency met -> Fills!
    fills_t3 = ee.process_tick(
        "MSFT", Decimal("300.0"), Decimal("305.0"), Decimal("298.0"), Decimal("302.0")
    )
    assert len(fills_t3) == 1
