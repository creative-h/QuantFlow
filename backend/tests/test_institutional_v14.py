"""Unit tests for QuantFlow v14.0 Institutional AI Trading Operating System."""

from datetime import datetime
import pytest

from app.analytics.ai_scoreboard import LiveAIScoreboard, ScoreboardMetrics
from app.analytics.confidence_calibration import CalibrationReport, ConfidenceCalibrator
from app.analytics.evening_coach import EveningAICoach, EveningCoachReport
from app.analytics.performance_lab import PerformanceLabEngine, PerformanceMetrics
from app.analytics.prediction_tracker import AIPredictionRecord, PredictionTracker
from app.marketdata.option_analytics import OptionAnalyticsEngine, StrikeAnalytics
from app.research.regime_classifier import DetailedRegimeClassifier, RegimeClassification
from app.research.strategy_lab import LabStrategyRank, StrategyLabEngine
from app.risk.portfolio_risk import PortfolioGreeks, PortfolioRiskEngine, PortfolioRiskMetrics


def test_prediction_tracker():
    tracker = PredictionTracker.get_instance()
    assert len(tracker.predictions) >= 1

    pred = AIPredictionRecord(
        prediction_id="PRED_TEST_99",
        timestamp=datetime.now(),
        symbol="NIFTY",
        spot=24915.20,
        option="NIFTY 24900 CE",
        direction="BUY",
        entry=118.0,
        stop_loss=105.0,
        target1=135.0,
        target2=155.0,
        confidence=90.0,
        probability=80.0,
        market_regime="STRONG_BULL",
        agent_votes={"TrendAgent": "BUY"},
        reason="EMA VWAP bounce",
        expected_holding_mins=20,
    )
    tracker.record_prediction(pred)
    assert any(p.prediction_id == "PRED_TEST_99" for p in tracker.predictions)

    acc = tracker.compute_accuracy_metrics()
    assert isinstance(acc, dict)
    assert "accuracy_pct" in acc


def test_live_ai_scoreboard():
    metrics = LiveAIScoreboard.get_scoreboard_metrics()
    assert isinstance(metrics, ScoreboardMetrics)
    assert metrics.win_rate > 70.0
    assert metrics.total_recommendations >= 10


def test_confidence_calibration():
    calib = ConfidenceCalibrator.calculate_calibration()
    assert isinstance(calib, CalibrationReport)
    assert calib.brier_score >= 0.0
    assert calib.expected_calibration_error < 0.10
    assert len(calib.reliability_bins) >= 4


def test_detailed_regime_classifier():
    reg = DetailedRegimeClassifier.classify_current_market()
    assert isinstance(reg, RegimeClassification)
    assert reg.regime in DetailedRegimeClassifier.REGIMES
    assert len(reg.recommended_strategies) >= 1


def test_option_analytics_engine():
    analytics = OptionAnalyticsEngine.get_strike_analytics(24915.20, 24900.0, "CE")
    assert isinstance(analytics, StrikeAnalytics)
    assert analytics.delta > 0.0
    assert analytics.gamma > 0.0
    assert analytics.intrinsic_value == 15.20


def test_portfolio_risk_engine():
    risk = PortfolioRiskEngine.get_portfolio_risk()
    assert isinstance(risk, PortfolioRiskMetrics)
    assert risk.greeks.portfolio_delta > 0.0
    assert risk.exposure_pct > 0.0


def test_performance_lab_engine():
    perf = PerformanceLabEngine.calculate_performance()
    assert isinstance(perf, PerformanceMetrics)
    assert perf.sharpe_ratio > 1.5
    assert perf.win_rate_pct > 70.0


def test_evening_ai_coach(tmp_path):
    report = EveningAICoach.generate_evening_report()
    assert isinstance(report, EveningCoachReport)
    assert len(report.insights) >= 1

    html_p = EveningAICoach.export_html_report(output_dir=str(tmp_path))
    assert html_p.exists()


def test_strategy_lab_engine():
    ranks = StrategyLabEngine.rank_all_strategies()
    assert len(ranks) >= 5
    assert ranks[0].composite_rank == 1
