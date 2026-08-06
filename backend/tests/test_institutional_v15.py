"""Unit tests for QuantFlow v15.0 Institutional Paper Trading Workstation & OMS."""

from datetime import datetime
import pytest

from app.marketdata.option_monitor import RealtimeOptionMonitor, RealtimeOptionSnapshot
from app.risk.portfolio_dashboard import SensibullPortfolioDashboard, SensibullPortfolioHeader
from app.trade_management.auto_exit_manager import AutoExitConfig, AutoExitManager, TradeManagerDecision
from app.trading_desk.broker_order_book import BrokerOrder, BrokerOrderBook, TradeBookEvent
from app.trading_desk.institutional_positions import InstitutionalPositionTracker, NetPositionItem, StrategyGroup
from app.trading_desk.position_details import DeepPositionDetails, PositionDetailsEngine, PositionExplainerOutput
from app.trading_desk.position_timeline import PositionTimelineEngine, PositionTimelineStep


def test_institutional_position_tracker():
    tracker = InstitutionalPositionTracker.get_instance()
    assert len(tracker.strategy_groups) >= 1
    totals = tracker.get_portfolio_totals()
    assert isinstance(totals, dict)
    assert "total_pnl" in totals
    assert "unbooked_pnl" in totals


def test_position_details_engine():
    details = PositionDetailsEngine.get_position_details("TRD_201")
    assert isinstance(details, DeepPositionDetails)
    assert details.explainer.why_entered is not None
    assert details.explainer.current_win_probability > 50.0


def test_auto_exit_manager():
    manager = AutoExitManager()
    # Test target 1 hit -> partial profit & break-even SL
    dec1 = manager.evaluate_position("TRD_201", current_price=250.0, entry_price=200.0, target1_price=245.0, sl_price=180.0, holding_time_mins=10.0)
    assert dec1.action == "BOOK_50"
    assert dec1.updated_sl == 200.0

    # Test time stop breach
    dec2 = manager.evaluate_position("TRD_201", current_price=210.0, entry_price=200.0, target1_price=245.0, sl_price=180.0, holding_time_mins=50.0)
    assert dec2.action == "BOOK_FULL"


def test_broker_order_book():
    book = BrokerOrderBook.get_instance()
    assert len(book.orders) >= 1
    assert len(book.events) >= 1

    evt = book.log_trade_event("TRD_201", "SL_MODIFIED", 218.50, 130, "SL moved to cost")
    assert isinstance(evt, TradeBookEvent)
    assert evt.event_type == "SL_MODIFIED"


def test_position_timeline_engine():
    timeline = PositionTimelineEngine.get_position_timeline("TRD_201")
    assert len(timeline) >= 8
    assert timeline[0].stage_name == "MARKET_SCAN"
    assert timeline[-1].stage_name == "REVIEW"


def test_realtime_option_monitor():
    snap = RealtimeOptionMonitor.get_live_snapshot("28th Jul 24250 CE", 24636.0)
    assert isinstance(snap, RealtimeOptionSnapshot)
    assert snap.intrinsic_value == 386.0
    assert snap.delta > 0.50


def test_sensibull_portfolio_dashboard():
    header = SensibullPortfolioDashboard.get_sensibull_header()
    assert isinstance(header, SensibullPortfolioHeader)
    assert header.total_pnl == -26810.0
    assert header.booked_pnl == 6522.0
