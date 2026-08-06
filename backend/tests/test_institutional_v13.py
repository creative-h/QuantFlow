"""Unit tests for QuantFlow Autonomous Institutional Paper Trading System."""

from datetime import datetime
import pytest

from app.analytics.backtest_comparison import BacktestComparisonEngine, BacktestVsPaperMetrics
from app.analytics.trade_explainability import NumericalTradeExplanation, NumericalTradeExplainer, PostTradeAudit
from app.marketdata.market_integrity import FeedCheckResult, MarketIntegrityEngine
from app.paper.realistic_broker import RealisticBroker, TradeExecutionCost
from app.system.health_monitor import AutonomousHealthMonitor, SystemHealthMetrics
from app.trading_desk.execution_pipeline import ExecutionPipeline
from app.trading_desk.live_trade_book import LiveTradeBook, TradeBookEntry


def test_market_integrity_engine():
    engine = MarketIntegrityEngine.get_instance()
    res = engine.validate_symbol_feeds("NIFTY", 24915.20, 24915.00, 24914.00)
    assert isinstance(res, FeedCheckResult)
    assert res.status == "VALID"

    res_warn = engine.validate_symbol_feeds("NIFTY", 24915.20, 24915.00, 24911.00)
    assert res_warn.status in ("VALID", "ACCEPTABLE_WARNING", "INVALID_DATA")


def test_execution_pipeline():
    pipe = ExecutionPipeline()
    status = pipe.get_pipeline_status()
    assert len(status) == 9
    pipe.advance_stage("Market Data")
    assert pipe.stages[0].is_completed is True


def test_live_trade_book():
    book = LiveTradeBook.get_instance()
    assert len(book.trades) >= 1
    updated = book.update_lifecycle("TB_001", "TARGET_HIT")
    assert updated is not None
    assert updated.trade_status == "TARGET_HIT"


def test_realistic_broker_friction():
    cost = RealisticBroker.calculate_execution("BUY", 118.0, 50)
    assert isinstance(cost, TradeExecutionCost)
    assert cost.brokerage == 20.0
    assert cost.gst > 0.0
    assert cost.total_charges > 20.0
    assert cost.execution_delay_ms == 50.0


def test_numerical_trade_explainer():
    exp = NumericalTradeExplainer.explain_trade_numerically("NIFTY", "BUY")
    assert isinstance(exp, NumericalTradeExplanation)
    assert exp.trend_score == 85.0
    assert exp.win_probability == 78.5

    audit = NumericalTradeExplainer.audit_completed_trade("TB_001", 1450.0)
    assert isinstance(audit, PostTradeAudit)
    assert audit.grade in ("A+", "A", "B", "C", "D")


def test_backtest_comparison_engine():
    comp = BacktestComparisonEngine.compare_performance()
    assert "win_rate" in comp
    assert comp["win_rate"].actual_value > 70.0


def test_autonomous_health_monitor():
    monitor = AutonomousHealthMonitor.get_instance()
    snap = monitor.get_health_snapshot()
    assert isinstance(snap, SystemHealthMetrics)
    assert snap.status in ("HEALTHY", "DEGRADED")
    assert snap.memory_usage_mb > 0.0
