"""Professional Portfolio tracking cash, equity, position values, and PnL metrics."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from loguru import logger

from app.models.trading import Side
from app.paper.portfolio.position import ProfessionalPosition
from app.paper.portfolio.trade import Trade


class ProfessionalPortfolio:
    """Tracks account cash balance, positions, trade executions, equity curve, and drawdown."""

    def __init__(self, initial_cash: float = 100000.0) -> None:
        self.initial_cash = Decimal(str(initial_cash))
        self.cash = Decimal(str(initial_cash))
        self.positions: dict[str, ProfessionalPosition] = {}
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple[datetime, Decimal]] = []
        self.peak_equity = Decimal(str(initial_cash))

    @property
    def total_unrealized_pnl(self) -> Decimal:
        """Sum of open unrealized PnL across positions."""
        return sum((pos.unrealized_pnl for pos in self.positions.values()), Decimal("0"))

    @property
    def total_realized_pnl(self) -> Decimal:
        """Sum of closed realized PnL across positions."""
        return sum((pos.realized_pnl for pos in self.positions.values()), Decimal("0"))

    @property
    def total_equity(self) -> Decimal:
        """Total current account equity."""
        pos_value = sum((pos.market_value for pos in self.positions.values()), Decimal("0"))
        return self.cash + pos_value

    @property
    def drawdown(self) -> Decimal:
        """Current drawdown amount from peak equity."""
        return max(Decimal("0"), self.peak_equity - self.total_equity)

    @property
    def drawdown_pct(self) -> float:
        """Current drawdown percentage from peak equity."""
        if self.peak_equity <= Decimal("0"):
            return 0.0
        return float(self.drawdown / self.peak_equity) * 100.0

    def update_market_price(
        self, symbol: str, price: Decimal, timestamp: Optional[datetime] = None
    ) -> None:
        """Update market price for symbol and recalculate equity & peak."""
        symbol_key = symbol.upper()
        if symbol_key not in self.positions:
            self.positions[symbol_key] = ProfessionalPosition(symbol_key)
        self.positions[symbol_key].update_market_price(price)

        current_eq = self.total_equity
        if current_eq > self.peak_equity:
            self.peak_equity = current_eq

        ts = timestamp or datetime.now(UTC)
        self.equity_curve.append((ts, current_eq))

    def record_fill(
        self,
        order_id: str,
        symbol: str,
        side: Side,
        quantity: int,
        fill_price: Decimal,
        commission: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
        timestamp: Optional[datetime] = None,
    ) -> Trade:
        """Record an executed trade fill and update cash and position."""
        symbol_key = symbol.upper()
        if symbol_key not in self.positions:
            self.positions[symbol_key] = ProfessionalPosition(symbol_key)

        pos = self.positions[symbol_key]
        signed_qty = quantity if side == Side.BUY else -quantity

        realized = pos.apply_fill(signed_qty, fill_price)

        cost = Decimal(quantity) * fill_price
        if side == Side.BUY:
            self.cash -= cost + commission
        else:
            self.cash += cost - commission

        trade = Trade(
            trade_id=str(uuid4()),
            order_id=order_id,
            symbol=symbol_key,
            side=side,
            quantity=quantity,
            price=fill_price,
            commission=commission,
            slippage=slippage,
            realized_pnl=realized,
            timestamp=timestamp or datetime.now(UTC),
        )
        self.trades.append(trade)
        logger.info(
            "Portfolio recorded fill for {} x {} @ {}. Realized PnL: {}",
            quantity,
            symbol_key,
            fill_price,
            realized,
        )
        return trade
