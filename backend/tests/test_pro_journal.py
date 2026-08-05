"""Unit tests for ProTradeJournal, HTML, JSON, and CSV exporters."""

from datetime import datetime
from pathlib import Path
import tempfile

import pytest

from app.analytics.multi_agent.decision import AITradeDecision
from app.paper.journal.pro_journal import ProJournalEntry, ProTradeJournal


@pytest.fixture
def sample_decision() -> AITradeDecision:
    return AITradeDecision(
        symbol="NIFTY",
        expiry="Thursday Weekly",
        strike=24900.0,
        option_type="CE",
        action="BUY",
        entry=118.0,
        stop_loss=105.0,
        target1=135.0,
        target2=155.0,
        target3=180.0,
        confidence=88.0,
        expected_hold_time="15-30 mins",
        risk_reward="1:2.7",
        reasons=["✓ EMA crossover confirmed"],
        warnings=[],
        market_regime="TRENDING_BULLISH",
    )


def test_pro_trade_journal_log_and_export(sample_decision):
    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "test_pro_journal.json"
        journal = ProTradeJournal(journal_file=json_file)

        entry = ProJournalEntry(
            trade_id="TR_001",
            symbol="NIFTY",
            contract_symbol="NIFTY 24900 CE",
            entry_time=datetime.now(),
            exit_time=datetime.now(),
            entry_price=118.0,
            exit_price=135.0,
            quantity=25,
            realized_pnl=425.0,
            duration_seconds=900.0,
            exit_reason="Target 1 Hit",
            ai_decision=sample_decision,
        )

        journal.log_trade_entry(entry)
        assert len(journal.entries) == 1

        # Test CSV Export
        csv_out = Path(tmpdir) / "export.csv"
        journal.export_csv(csv_out)
        assert csv_out.exists()
        assert csv_out.stat().st_size > 0

        # Test JSON Export
        json_out = Path(tmpdir) / "export.json"
        journal.export_json(json_out)
        assert json_out.exists()
        assert json_out.stat().st_size > 0
