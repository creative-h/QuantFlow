"""Order lifecycle manager for paper execution."""

from typing import Optional

from app.models.trading import Order, OrderStatus


class OrderManager:
    """Tracks and updates order lifecycle states."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def add_order(self, order: Order) -> None:
        """Add a new order record."""
        self._orders[order.id] = order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Retrieve order by ID."""
        return self._orders.get(order_id)

    def list_orders(
        self, status: Optional[OrderStatus] = None, symbol: Optional[str] = None
    ) -> list[Order]:
        """List orders filtered by status or symbol."""
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        if symbol:
            orders = [o for o in orders if o.request.symbol.upper() == symbol.upper()]
        return orders

    def update_order(self, order: Order) -> None:
        """Update an existing order record."""
        self._orders[order.id] = order
