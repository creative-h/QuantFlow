"""Paper order storage."""

from app.models.trading import Order, OrderStatus


class PaperOrderBook:
    """Store and query paper orders by identifier."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def add(self, order: Order) -> None:
        self._orders[order.id] = order

    def cancel(self, order_id: str) -> Order:
        order = self._orders[order_id]
        order.status = OrderStatus.CANCELLED
        return order

    def all(self) -> list[Order]:
        return list(self._orders.values())
