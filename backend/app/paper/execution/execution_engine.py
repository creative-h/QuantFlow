"""Execution Engine managing order queues, latency simulation, and candle tick processing."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from loguru import logger

from app.models.trading import Order, OrderRequest, OrderStatus
from app.paper.execution.fill_engine import FillEngine, FillResult
from app.paper.execution.order_manager import OrderManager
from app.paper.execution.validator import OrderValidator, OrderValidationError


class ExecutionEngine:
    """Manages order submission, queued execution with simulated latency, and fill evaluation."""

    def __init__(
        self,
        order_manager: Optional[OrderManager] = None,
        fill_engine: Optional[FillEngine] = None,
        validator: Optional[OrderValidator] = None,
        latency_ticks: int = 0,
    ) -> None:
        self.order_manager = order_manager or OrderManager()
        self.fill_engine = fill_engine or FillEngine()
        self.validator = validator or OrderValidator()
        self.latency_ticks = latency_ticks
        self._pending_queue: list[tuple[Order, int]] = []
        self._tick_counter = 0

    def submit_order(
        self,
        request: OrderRequest,
        available_cash: Decimal,
        current_price: Optional[Decimal] = None,
    ) -> Order:
        """Validate and queue order for execution."""
        try:
            self.validator.validate(request, available_cash, current_price)
        except OrderValidationError as err:
            logger.warning("Order validation failed for {}: {}", request.symbol, str(err))
            rejected_order = Order(
                id=str(uuid4()),
                request=request,
                status=OrderStatus.REJECTED,
                filled_quantity=0,
                average_price=None,
                created_at=datetime.now(UTC),
            )
            self.order_manager.add_order(rejected_order)
            return rejected_order

        order = Order(
            id=str(uuid4()),
            request=request,
            status=OrderStatus.OPEN,
            filled_quantity=0,
            average_price=None,
            created_at=datetime.now(UTC),
        )
        self.order_manager.add_order(order)
        self._pending_queue.append((order, self._tick_counter))
        logger.info("Submitted order {} for {} x {}", order.id, request.quantity, request.symbol)
        return order

    def process_tick(
        self,
        symbol: str,
        open_price: Decimal,
        high_price: Decimal,
        low_price: Decimal,
        close_price: Decimal,
    ) -> list[tuple[Order, FillResult]]:
        """Advance tick counter and evaluate fills for active orders matching symbol."""
        self._tick_counter += 1
        fills: list[tuple[Order, FillResult]] = []
        remaining_queue: list[tuple[Order, int]] = []

        for order, submitted_tick in self._pending_queue:
            if order.request.symbol.upper() != symbol.upper():
                remaining_queue.append((order, submitted_tick))
                continue

            # Check simulated exchange latency
            if (self._tick_counter - submitted_tick) < self.latency_ticks:
                remaining_queue.append((order, submitted_tick))
                continue

            result = self.fill_engine.evaluate_fill(
                request=order.request,
                current_open=open_price,
                current_high=high_price,
                current_low=low_price,
                current_close=close_price,
                already_filled_qty=order.filled_quantity,
            )

            if result.filled:
                order.filled_quantity += result.fill_quantity
                order.average_price = result.fill_price

                if order.filled_quantity >= order.request.quantity:
                    order.status = OrderStatus.FILLED
                else:
                    order.status = OrderStatus.OPEN

                self.order_manager.update_order(order)
                fills.append((order, result))

                if order.status != OrderStatus.FILLED:
                    remaining_queue.append((order, submitted_tick))
            else:
                remaining_queue.append((order, submitted_tick))

        self._pending_queue = remaining_queue
        return fills
