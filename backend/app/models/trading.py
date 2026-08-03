"""Broker-neutral trading domain models."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"


class OrderStatus(StrEnum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    side: Side
    order_type: OrderType = OrderType.MARKET
    price: Decimal | None = Field(default=None, gt=0)


class Order(BaseModel):
    id: str
    request: OrderRequest
    status: OrderStatus
    filled_quantity: int = 0
    average_price: Decimal | None = None
    created_at: datetime


class Position(BaseModel):
    symbol: str
    quantity: int
    average_price: Decimal
    last_price: Decimal | None = None


class Holding(BaseModel):
    symbol: str
    quantity: int
    average_price: Decimal


class Profile(BaseModel):
    user_id: str
    user_name: str
    email: str | None = None
