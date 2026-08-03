"""Order validator for paper execution."""

from decimal import Decimal
from typing import Optional

from loguru import logger

from app.models.trading import OrderRequest, OrderType


class OrderValidationError(ValueError):
    """Raised when an order request fails validation."""

    pass


class OrderValidator:
    """Validates order requests against basic parameters and account purchasing power."""

    def __init__(self, allow_shorting: bool = True) -> None:
        self.allow_shorting = allow_shorting

    def validate(
        self,
        request: OrderRequest,
        available_cash: Decimal,
        current_price: Optional[Decimal] = None,
    ) -> None:
        """Validate order request parameters and account balance."""
        if not request.symbol or not request.symbol.strip():
            raise OrderValidationError("Order symbol cannot be empty")

        if request.quantity <= 0:
            raise OrderValidationError(f"Invalid quantity {request.quantity}: must be positive")

        if request.order_type == OrderType.LIMIT and (
            request.price is None or request.price <= Decimal("0")
        ):
            raise OrderValidationError("LIMIT order requires a positive price")

        exec_price = request.price if request.price else (current_price or Decimal("100.0"))
        required_funds = Decimal(request.quantity) * exec_price

        if request.side.value == "BUY" and required_funds > available_cash:
            logger.warning(
                "Order rejected: Insufficient funds. Required: {}, Available: {}",
                required_funds,
                available_cash,
            )
            raise OrderValidationError(
                f"Insufficient funds: Order requires {required_funds}, available cash is {available_cash}"
            )

        logger.debug(
            "Order request for {} x {} validated successfully", request.quantity, request.symbol
        )
