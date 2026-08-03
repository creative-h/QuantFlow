"""Kite order translation helpers."""

from datetime import UTC, datetime
from decimal import Decimal

from app.models.trading import Order, OrderRequest, OrderStatus, OrderType, Side


def to_order(payload: dict[str, object], request: OrderRequest) -> Order:
    """Translate a Kite order response to the domain order model."""

    return Order(
        id=str(payload["order_id"]),
        request=request,
        status=OrderStatus(str(payload.get("status", "OPEN")).upper()),
        created_at=datetime.now(UTC),
        average_price=Decimal(str(payload.get("average_price") or "0")),
    )


def to_domain_order(payload: dict[str, object]) -> Order:
    """Translate a Kite order-history item into a domain order."""

    raw_status = str(payload.get("status", "OPEN")).upper()
    status = OrderStatus(raw_status if raw_status in {item.value for item in OrderStatus} else "OPEN")
    raw_price = payload.get("price")
    request = OrderRequest(
        symbol=str(payload["tradingsymbol"]),
        quantity=int(payload["quantity"]),
        side=Side(str(payload["transaction_type"]).upper()),
        order_type=OrderType(str(payload["order_type"]).upper()),
        price=Decimal(str(raw_price)) if raw_price and Decimal(str(raw_price)) > 0 else None,
    )
    timestamp = str(payload.get("order_timestamp") or datetime.now(UTC).isoformat())
    return Order(
        id=str(payload["order_id"]),
        request=request,
        status=status,
        filled_quantity=int(payload.get("filled_quantity") or 0),
        average_price=Decimal(str(payload["average_price"])) if payload.get("average_price") else None,
        created_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
    )
