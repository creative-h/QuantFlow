"""Paper trading broker implementing abstract Broker interface."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from loguru import logger

from app.brokers.base import Broker
from app.models.trading import (
    Holding,
    Order,
    OrderRequest,
    OrderStatus,
    Position,
    Profile,
    Side,
)
from app.paper.execution.execution_engine import ExecutionEngine
from app.paper.journal.trade_journal import TradeJournal
from app.paper.portfolio.portfolio import ProfessionalPortfolio
from app.risk.manager import RiskManager


class PaperBroker(Broker):
    """In-memory professional paper trading broker adapter adhering to abstract Broker interface."""

    def __init__(
        self,
        initial_cash: float = 100000.0,
        user_id: str = "PAPER_USER",
        execution_engine: Optional[ExecutionEngine] = None,
        risk_manager: Optional[RiskManager] = None,
    ) -> None:
        self.user_id = user_id
        self.portfolio = ProfessionalPortfolio(initial_cash)
        self.execution_engine = execution_engine or ExecutionEngine()
        self.risk_manager = risk_manager or RiskManager()
        self.journal = TradeJournal()
        self._last_prices: dict[str, Decimal] = {}

    @property
    def cash(self) -> Decimal:
        return self.portfolio.cash

    @cash.setter
    def cash(self, value: Decimal) -> None:
        self.portfolio.cash = value

    async def login(self, request_token: str = "") -> str:
        """Paper broker does not require authentication; returns mock token."""
        logger.info("PaperBroker session initiated for user {}", self.user_id)
        return "mock_paper_access_token"

    async def profile(self) -> Profile:
        """Return paper trading account profile."""
        return Profile(
            user_id=self.user_id,
            user_name="Paper Trader",
            email="paper@quantflow.local",
        )

    def set_last_price(self, symbol: str, price: float | Decimal) -> None:
        """Update last market price for paper order execution and PnL."""
        dec_price = Decimal(str(price))
        self._last_prices[symbol.upper()] = dec_price
        self.portfolio.update_market_price(symbol, dec_price)

    async def place_order(self, order: OrderRequest) -> Order:
        """Evaluate pre-trade risk and submit paper order request."""
        symbol = order.symbol.upper()
        current_price = self._last_prices.get(symbol, order.price or Decimal("100.0"))

        approved, reason = self.risk_manager.evaluate_order(order, self.portfolio)
        if not approved:
            rejected_order = Order(
                id=str(uuid4()),
                request=order,
                status=OrderStatus.REJECTED,
                filled_quantity=0,
                average_price=None,
                created_at=datetime.now(UTC),
            )
            self.execution_engine.order_manager.add_order(rejected_order)
            return rejected_order

        # Submit order to execution engine
        submitted_order = self.execution_engine.submit_order(
            order, available_cash=self.portfolio.cash, current_price=current_price
        )

        if submitted_order.status == OrderStatus.REJECTED:
            return submitted_order

        # Execute immediate fill for market price matching current tick
        fills = self.execution_engine.process_tick(
            symbol=symbol,
            open_price=current_price,
            high_price=current_price,
            low_price=current_price,
            close_price=current_price,
        )

        for filled_order, fill_res in fills:
            trade = self.portfolio.record_fill(
                order_id=filled_order.id,
                symbol=symbol,
                side=order.side,
                quantity=fill_res.fill_quantity,
                fill_price=fill_res.fill_price,
                commission=fill_res.commission,
                slippage=fill_res.slippage,
            )
            self.journal.log_trade(trade)

        return submitted_order

    async def cancel_order(self, order_id: str) -> Order:
        """Cancel an existing order if open."""
        order = self.execution_engine.order_manager.get_order(order_id)
        if order:
            if order.status == OrderStatus.OPEN:
                order.status = OrderStatus.CANCELLED
                self.execution_engine.order_manager.update_order(order)
                logger.info("PaperBroker cancelled order {}", order_id)
            return order

        dummy_req = OrderRequest(symbol="UNKNOWN", quantity=1, side=Side.BUY)
        return Order(
            id=order_id,
            request=dummy_req,
            status=OrderStatus.CANCELLED,
            filled_quantity=0,
            average_price=None,
            created_at=datetime.now(UTC),
        )

    async def positions(self) -> list[Position]:
        """Return active positions."""
        result = []
        for symbol, pos in self.portfolio.positions.items():
            if pos.quantity != 0:
                result.append(
                    Position(
                        symbol=symbol,
                        quantity=pos.quantity,
                        average_price=pos.average_price,
                        last_price=pos.last_price,
                    )
                )
        return result

    async def holdings(self) -> list[Holding]:
        """Return long positions."""
        result = []
        for symbol, pos in self.portfolio.positions.items():
            if pos.quantity > 0:
                result.append(
                    Holding(
                        symbol=symbol,
                        quantity=pos.quantity,
                        average_price=pos.average_price,
                    )
                )
        return result

    async def orders(self) -> list[Order]:
        """Return history of all orders."""
        return self.execution_engine.order_manager.list_orders()
