"""In-memory virtual portfolio."""

from decimal import Decimal


class PaperPortfolio:
    """Track cash, positions, and realised profit and loss."""

    def __init__(self, initial_cash: Decimal) -> None:
        self.cash = initial_cash
        self.positions: dict[str, int] = {}
        self.realised_pnl = Decimal("0")

    def apply_fill(self, symbol: str, quantity: int, price: Decimal) -> None:
        """Apply signed quantity (positive buy, negative sell) at a fill price."""

        self.cash -= Decimal(quantity) * price
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity

    def equity(self, prices: dict[str, Decimal]) -> Decimal:
        """Return marked-to-market portfolio equity."""

        return self.cash + sum(Decimal(quantity) * prices.get(symbol, Decimal("0")) for symbol, quantity in self.positions.items())
