"""Unit tests for TradeJournal."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models.trading import Side
from app.paper.journal.trade_journal import TradeJournal
from app.paper.portfolio.trade import Trade


def test_trade_journal_log_and_snapshot():
    journal = TradeJournal()

    trade = Trade(
        trade_id="t1",
        order_id="o1",
        symbol="NFLX",
        side=Side.BUY,
        quantity=10,
        price=Decimal("400.0"),
        commission=Decimal("2.5"),
        slippage=Decimal("0.5"),
        realized_pnl=Decimal("0.0"),
        timestamp=datetime(2024, 1, 15, 10, 0),
    )

    entry = journal.log_trade(trade, notes="Earnings momentum entry")
    assert entry.trade_id == "t1"
    assert entry.notes == "Earnings momentum entry"
    assert len(journal.entries) == 1

    journal.record_snapshot(
        timestamp=datetime(2024, 1, 15, 10, 0),
        equity=Decimal("10000.0"),
        cash=Decimal("6000.0"),
        drawdown=Decimal("0.0"),
    )
    assert len(journal.equity_snapshots) == 1


def test_trade_journal_to_dataframe():
    journal = TradeJournal()
    df_empty = journal.to_dataframe()
    assert df_empty.empty
    assert "trade_id" in df_empty.columns

    trade = Trade(
        trade_id="t2",
        order_id="o2",
        symbol="NFLX",
        side=Side.SELL,
        quantity=10,
        price=Decimal("420.0"),
        commission=Decimal("2.5"),
        slippage=Decimal("0.5"),
        realized_pnl=Decimal("200.0"),
        timestamp=datetime(2024, 1, 16, 10, 0),
    )
    journal.log_trade(trade)
    df = journal.to_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["realized_pnl"] == 200.0
