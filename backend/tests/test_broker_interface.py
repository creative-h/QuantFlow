"""Unit tests for abstract Broker interface and PaperBroker implementation."""

from decimal import Decimal

import pytest

from app.brokers.base import Broker
from app.brokers.paper_broker import PaperBroker
from app.brokers.zerodha.broker import ZerodhaBroker
from app.models.trading import OrderRequest, OrderStatus, Side


@pytest.fixture
def paper_broker() -> PaperBroker:
    return PaperBroker(initial_cash=100000.0, user_id="TEST_TRADER")


def test_broker_subclasses():
    assert issubclass(PaperBroker, Broker)
    assert issubclass(ZerodhaBroker, Broker)


@pytest.mark.asyncio
async def test_paper_broker_login(paper_broker: PaperBroker):
    token = await paper_broker.login("any_request_token")
    assert token == "mock_paper_access_token"


@pytest.mark.asyncio
async def test_paper_broker_profile(paper_broker: PaperBroker):
    profile = await paper_broker.profile()
    assert profile.user_id == "TEST_TRADER"
    assert profile.user_name == "Paper Trader"


@pytest.mark.asyncio
async def test_paper_broker_place_and_list_orders(paper_broker: PaperBroker):
    req = OrderRequest(symbol="RELIANCE", quantity=10, side=Side.BUY, price=Decimal("2500.0"))
    order = await paper_broker.place_order(req)

    assert order.status == OrderStatus.FILLED
    assert order.filled_quantity == 10
    assert order.average_price >= Decimal("2500.0")

    orders = await paper_broker.orders()
    assert len(orders) == 1
    assert orders[0].id == order.id

    positions = await paper_broker.positions()
    assert len(positions) == 1
    assert positions[0].symbol == "RELIANCE"
    assert positions[0].quantity == 10

    holdings = await paper_broker.holdings()
    assert len(holdings) == 1
    assert holdings[0].symbol == "RELIANCE"


@pytest.mark.asyncio
async def test_paper_broker_cancel_order(paper_broker: PaperBroker):
    req = OrderRequest(symbol="TCS", quantity=5, side=Side.BUY, price=Decimal("3500.0"))
    order = await paper_broker.place_order(req)

    cancelled = await paper_broker.cancel_order(order.id)
    assert cancelled.id == order.id
