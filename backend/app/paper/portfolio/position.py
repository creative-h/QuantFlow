"""Professional position tracking class."""

from decimal import Decimal


class ProfessionalPosition:
    """Tracks position quantity, cost basis, average price, market value, realized & unrealized PnL."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol.upper()
        self.quantity: int = 0
        self.average_price: Decimal = Decimal("0")
        self.last_price: Decimal = Decimal("0")
        self.realized_pnl: Decimal = Decimal("0")

    @property
    def cost_basis(self) -> Decimal:
        """Total cost basis of current position."""
        return Decimal(abs(self.quantity)) * self.average_price

    @property
    def market_value(self) -> Decimal:
        """Current market value of position."""
        return Decimal(self.quantity) * self.last_price

    @property
    def unrealized_pnl(self) -> Decimal:
        """Current open unrealized profit/loss."""
        if self.quantity == 0:
            return Decimal("0")
        return (self.last_price - self.average_price) * Decimal(self.quantity)

    def update_market_price(self, price: Decimal) -> None:
        """Update last market price."""
        self.last_price = price

    def apply_fill(self, fill_qty: int, fill_price: Decimal) -> Decimal:
        """Apply fill, update average price / cost basis, and return realized PnL."""
        self.last_price = fill_price
        realized = Decimal("0")

        if self.quantity == 0:
            self.quantity = fill_qty
            self.average_price = fill_price
        elif (self.quantity > 0 and fill_qty > 0) or (self.quantity < 0 and fill_qty < 0):
            # Increasing position size
            total_qty = self.quantity + fill_qty
            total_cost = (Decimal(self.quantity) * self.average_price) + (
                Decimal(fill_qty) * fill_price
            )
            self.quantity = total_qty
            self.average_price = total_cost / Decimal(total_qty)
        else:
            # Reducing or closing position
            closed_qty = min(abs(self.quantity), abs(fill_qty))
            if self.quantity > 0:
                realized = Decimal(closed_qty) * (fill_price - self.average_price)
            else:
                realized = Decimal(closed_qty) * (self.average_price - fill_price)

            self.realized_pnl += realized
            self.quantity += fill_qty

            if self.quantity == 0:
                self.average_price = Decimal("0")

        return realized
