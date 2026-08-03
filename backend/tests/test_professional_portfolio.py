"""Unit tests for ProfessionalPortfolio and ProfessionalPosition."""

from decimal import Decimal

import pytest

from app.models.trading import Side
from app.paper.portfolio.portfolio import ProfessionalPortfolio
from app.paper.portfolio.position import ProfessionalPosition


def test_position_tracking_and_realized_pnl():
    pos = ProfessionalPosition("NVDA")
    assert pos.quantity == 0
    assert pos.realized_pnl == Decimal("0")

    # Buy 10 @ 100
    pos.apply_fill(10, Decimal("100.0"))
    assert pos.quantity == 10
    assert pos.average_price == Decimal("100.0")

    # Update market price to 120
    pos.update_market_price(Decimal("120.0"))
    assert pos.unrealized_pnl == Decimal("200.0")
    assert pos.market_value == Decimal("1200.0")

    # Sell 5 @ 130 -> Realized PnL = 5 * (130 - 100) = 150
    realized = pos.apply_fill(-5, Decimal("130.0"))
    assert realized == Decimal("150.0")
    assert pos.realized_pnl == Decimal("150.0")
    assert pos.quantity == 5


def test_portfolio_equity_and_drawdown():
    port = ProfessionalPortfolio(initial_cash=10000.0)
    assert port.total_equity == Decimal("10000.0")
    assert port.drawdown == Decimal("0")

    # Record Buy fill 10 @ 100 -> Cash = 9000, Position val = 1000, Total Eq = 10000
    port.record_fill(
        order_id="1", symbol="NVDA", side=Side.BUY, quantity=10, fill_price=Decimal("100.0")
    )
    assert port.cash == Decimal("9000.0")
    assert port.total_equity == Decimal("10000.0")

    # Price drops to 80 -> Position val = 800, Equity = 9800, Peak = 10000, DD = 200 (2%)
    port.update_market_price("NVDA", Decimal("80.0"))
    assert port.total_equity == Decimal("9800.0")
    assert port.drawdown == Decimal("200.0")
    assert pytest.approx(port.drawdown_pct, 0.01) == 2.0


def test_portfolio_trade_recording():
    port = ProfessionalPortfolio(initial_cash=10000.0)
    trade = port.record_fill(
        order_id="tx1",
        symbol="GOOGL",
        side=Side.BUY,
        quantity=5,
        fill_price=Decimal("150.0"),
        commission=Decimal("2.0"),
        slippage=Decimal("0.5"),
    )
    assert trade.symbol == "GOOGL"
    assert trade.quantity == 5
    assert trade.commission == Decimal("2.0")
    assert len(port.trades) == 1
