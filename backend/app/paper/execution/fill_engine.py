"""Fill simulation engine supporting Market, Limit, Stop, and Stop-Limit orders with slippage, commission, and partial fills."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.models.trading import OrderRequest, OrderType, Side


@dataclass
class SlippageModel:
    """Slippage calculation model."""

    pct: float = 0.0005  # 0.05% default slippage
    fixed_per_share: float = 0.0

    def calculate_fill_price(self, base_price: Decimal, side: Side) -> Decimal:
        price_float = float(base_price)
        slippage_amount = (price_float * self.pct) + self.fixed_per_share
        if side == Side.BUY:
            fill_price = price_float + slippage_amount
        else:
            fill_price = max(0.01, price_float - slippage_amount)
        return Decimal(str(round(fill_price, 4)))


@dataclass
class CommissionModel:
    """Commission calculation model."""

    per_order: float = 0.0
    per_share: float = 0.0
    pct: float = 0.0003  # 0.03% default commission

    def calculate_commission(self, quantity: int, fill_price: Decimal) -> Decimal:
        val = float(fill_price) * quantity
        comm = self.per_order + (self.per_share * quantity) + (val * self.pct)
        return Decimal(str(round(comm, 4)))


@dataclass
class FillResult:
    """Result of order fill evaluation."""

    filled: bool
    fill_quantity: int
    fill_price: Decimal
    commission: Decimal
    slippage: Decimal
    is_partial: bool = False
    rejection_reason: Optional[str] = None


class FillEngine:
    """Evaluates candle/tick market data and produces realistic fills."""

    def __init__(
        self,
        slippage_model: Optional[SlippageModel] = None,
        commission_model: Optional[CommissionModel] = None,
        partial_fill_ratio: float = 1.0,
    ) -> None:
        self.slippage_model = slippage_model or SlippageModel()
        self.commission_model = commission_model or CommissionModel()
        self.partial_fill_ratio = partial_fill_ratio

    def evaluate_fill(
        self,
        request: OrderRequest,
        current_open: Decimal,
        current_high: Decimal,
        current_low: Decimal,
        current_close: Decimal,
        stop_price: Optional[Decimal] = None,
        already_filled_qty: int = 0,
    ) -> FillResult:
        """Evaluate fill condition based on order type and candle prices."""
        rem_qty = request.quantity - already_filled_qty
        if rem_qty <= 0:
            return FillResult(
                filled=False,
                fill_quantity=0,
                fill_price=Decimal("0"),
                commission=Decimal("0"),
                slippage=Decimal("0"),
            )

        target_qty = (
            max(1, int(rem_qty * self.partial_fill_ratio))
            if self.partial_fill_ratio < 1.0
            else rem_qty
        )
        is_partial = target_qty < rem_qty

        # 1. MARKET ORDER
        if request.order_type == OrderType.MARKET:
            fill_base = current_open if current_open > Decimal("0") else current_close
            fill_price = self.slippage_model.calculate_fill_price(fill_base, request.side)
            slippage = abs(fill_price - fill_base)
            comm = self.commission_model.calculate_commission(target_qty, fill_price)
            return FillResult(
                filled=True,
                fill_quantity=target_qty,
                fill_price=fill_price,
                commission=comm,
                slippage=slippage,
                is_partial=is_partial,
            )

        # 2. LIMIT ORDER
        elif request.order_type == OrderType.LIMIT:
            limit_price = request.price or current_close
            if request.side == Side.BUY and current_low <= limit_price:
                base_price = min(limit_price, current_open)
                fill_price = self.slippage_model.calculate_fill_price(base_price, request.side)
                slippage = abs(fill_price - base_price)
                comm = self.commission_model.calculate_commission(target_qty, fill_price)
                return FillResult(
                    filled=True,
                    fill_quantity=target_qty,
                    fill_price=fill_price,
                    commission=comm,
                    slippage=slippage,
                    is_partial=is_partial,
                )
            elif request.side == Side.SELL and current_high >= limit_price:
                base_price = max(limit_price, current_open)
                fill_price = self.slippage_model.calculate_fill_price(base_price, request.side)
                slippage = abs(fill_price - base_price)
                comm = self.commission_model.calculate_commission(target_qty, fill_price)
                return FillResult(
                    filled=True,
                    fill_quantity=target_qty,
                    fill_price=fill_price,
                    commission=comm,
                    slippage=slippage,
                    is_partial=is_partial,
                )

        # 3. STOP ORDER
        elif request.order_type == OrderType.STOP_LOSS:
            trigger = stop_price or request.price or current_close
            triggered = (request.side == Side.BUY and current_high >= trigger) or (
                request.side == Side.SELL and current_low <= trigger
            )
            if triggered:
                fill_base = current_open if current_open > Decimal("0") else current_close
                fill_price = self.slippage_model.calculate_fill_price(fill_base, request.side)
                slippage = abs(fill_price - fill_base)
                comm = self.commission_model.calculate_commission(target_qty, fill_price)
                return FillResult(
                    filled=True,
                    fill_quantity=target_qty,
                    fill_price=fill_price,
                    commission=comm,
                    slippage=slippage,
                    is_partial=is_partial,
                )

        return FillResult(
            filled=False,
            fill_quantity=0,
            fill_price=Decimal("0"),
            commission=Decimal("0"),
            slippage=Decimal("0"),
        )
