"""Immediate-fill paper execution engine."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.models.trading import Order, OrderRequest, OrderStatus, Side
from app.paper.orderbook import PaperOrderBook
from app.paper.portfolio import PaperPortfolio


class PaperTradingEngine:
    """Fill marketable paper orders at a supplied market price."""

    def __init__(self, portfolio: PaperPortfolio, orderbook: PaperOrderBook) -> None:
        self.portfolio = portfolio
        self.orderbook = orderbook

    def execute(self, request: OrderRequest, market_price: Decimal) -> Order:
        """Create and immediately fill an order at the current price."""

        signed_quantity = request.quantity if request.side is Side.BUY else -request.quantity
        self.portfolio.apply_fill(request.symbol, signed_quantity, market_price)
        order = Order(id=str(uuid4()), request=request, status=OrderStatus.FILLED, filled_quantity=request.quantity, average_price=market_price, created_at=datetime.now(UTC))
        self.orderbook.add(order)
        return order
