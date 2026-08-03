"""Trade execution record model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.models.trading import Side


@dataclass
class Trade:
    """Record of an executed trade fill."""

    trade_id: str
    order_id: str
    symbol: str
    side: Side
    quantity: int
    price: Decimal
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    timestamp: Optional[datetime] = None
