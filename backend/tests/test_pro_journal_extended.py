"""Extended Unit Tests for ProTradeJournal persistence and multi-entry logging."""

from datetime import datetime
from pathlib import Path
import tempfile
import pytest

from app.analytics.multi_agent.decision import AITradeDecision
from app.paper.journal.pro_journal import ProJournalEntry, ProTradeJournal


def test_pro_journal_multiple_entries_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        jfile = Path(tmpdir) / "multi_journal.json"
        journal1 = ProTradeJournal(journal_file=jfile)

        dec = AITradeDecision(
            symbol="BANKNIFTY",
            expiry="Thursday Weekly",
            strike=55000.0,
            option_type="PE",
            action="BUY",
            entry=115.0,
            stop_loss=102.0,
            target1=132.0,
            target2=150.0,
            target3=175.0,
            confidence=85.0,
            expected_hold_time="15-30 mins",
            risk_reward="1:2.5",
        )

        for i in range(5):
            e = ProJournalEntry(
                trade_id=f"TR_10{i}",
                symbol="BANKNIFTY",
                contract_symbol="BANKNIFTY 55000 PE",
                entry_time=datetime.now(),
                exit_time=datetime.now(),
                entry_price=115.0,
                exit_price=132.0,
                quantity=15,
                realized_pnl=255.0 * (i + 1),
                duration_seconds=600.0,
                exit_reason="Target 1 Hit",
                ai_decision=dec,
            )
            journal1.log_trade_entry(e)

        assert len(journal1.entries) == 5

        # Reload in new instance
        journal2 = ProTradeJournal(journal_file=jfile)
        assert len(journal2.entries) == 5
        assert journal2.entries[0].trade_id == "TR_100"
        assert journal2.entries[4].realized_pnl == 1275.0
