"""Risk Manager enforcing trading rules and account safety limits."""

from decimal import Decimal
from typing import Optional

from loguru import logger

from app.models.trading import OrderRequest
from app.paper.portfolio.portfolio import ProfessionalPortfolio
from app.risk.rules import TradingRules


class RiskManager:
    """Pre-trade risk validator evaluating order requests against portfolio state and TradingRules."""

    def __init__(self, rules: Optional[TradingRules] = None) -> None:
        self.rules = rules or TradingRules()

    def evaluate_order(
        self, request: OrderRequest, portfolio: ProfessionalPortfolio
    ) -> tuple[bool, str]:
        """Evaluate order against account equity, position sizes, and drawdown limits."""
        pos = portfolio.positions.get(request.symbol.upper())
        current_qty = pos.quantity if pos else 0
        current_drawdown_pct = portfolio.drawdown_pct
        price = request.price or Decimal("100.0")

        approved, reason = self.rules.validate_order(
            symbol=request.symbol,
            quantity=request.quantity,
            price=price,
            current_position_qty=current_qty,
            current_drawdown_pct=current_drawdown_pct,
        )

        if not approved:
            logger.warning("RiskManager REJECTED order for {}: {}", request.symbol, reason)
        else:
            logger.debug("RiskManager APPROVED order for {}", request.symbol)

        return approved, reason
