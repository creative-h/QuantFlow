"""Unit tests for QuantFlow v12.0 Professional Trade Desk & Audit Engine."""

from datetime import datetime
import pytest

from app.trading_desk.order_audit_log import AuditEvent, OrderAuditLogger
from app.trading_desk.position_tracker import ClosedPosition, OpenPosition, PositionTracker
from app.trading_desk.rejected_trades import RejectedTrade, RejectedTradeLogger
from app.trading_desk.session_summary import SessionSummary, SessionSummaryGenerator
from app.trading_desk.telegram_notifier import TelegramAlert, TelegramNotifier


def test_order_audit_logger():
    logger = OrderAuditLogger.get_instance()
    evt = logger.log_event("TEST_EVENT", "NIFTY", "Test audit event details.")
    assert isinstance(evt, AuditEvent)
    assert evt.event_type == "TEST_EVENT"
    assert evt.symbol == "NIFTY"
    assert len(logger.get_recent_events()) >= 1


def test_rejected_trade_logger():
    logger = RejectedTradeLogger.get_instance()
    rej = logger.log_rejection("NIFTY 24900 PE", "BUY", "PCR below threshold", "PCRAgent")
    assert isinstance(rej, RejectedTrade)
    assert rej.instrument == "NIFTY 24900 PE"
    assert rej.rejected_by == "PCRAgent"
    assert len(logger.get_all_rejections()) >= 1


def test_position_tracker_open_and_close():
    tracker = PositionTracker.get_instance()
    assert len(tracker.open_positions) >= 1

    pos = OpenPosition(
        trade_id="TRD_999",
        time=datetime.now(),
        underlying="NIFTY",
        option="NIFTY 24900 CE",
        side="BUY",
        quantity=50,
        entry_price=100.0,
        current_price=110.0,
        pnl=500.0,
        pnl_pct=10.0,
        stop_loss=90.0,
        target1=120.0,
        target2=140.0,
        target3=160.0,
        current_rr=2.0,
        holding_time_mins=10.0,
    )
    tracker.add_open_position(pos)
    assert any(p.trade_id == "TRD_999" for p in tracker.open_positions)

    closed = tracker.close_position("TRD_999", exit_price=120.0, exit_reason="TARGET_1_HIT")
    assert isinstance(closed, ClosedPosition)
    assert closed.pnl == 1000.0
    assert closed.exit_reason == "TARGET_1_HIT"


def test_telegram_notifier():
    notifier = TelegramNotifier.get_instance()
    alert = notifier.notify_trade_entry("NIFTY", "BUY", 118.0, 105.0, 145.0, 91.0)
    assert isinstance(alert, TelegramAlert)
    assert alert.alert_type == "TRADE_ENTRY"
    assert alert.sent is True


def test_session_summary_generator():
    summary = SessionSummaryGenerator.generate_session_summary()
    assert isinstance(summary, SessionSummary)
    assert summary.net_pnl == 4250.0
    assert summary.win_rate == 80.0
    assert len(summary.equity_curve) >= 5
