"""Unit tests for QuantFlow v10.0 AI Trading Coach Engine & Performance Auditor."""

import pytest

from app.analytics.coach_engine import AITradingCoachEngine, LessonsLearned, SetupMatchResult, TradeExplanation
from app.analytics.performance_auditor import AuditReport, PerformanceAuditor


def test_ai_trading_coach_explain_trade():
    exp = AITradingCoachEngine.explain_trade(symbol="NIFTY", action="BUY", entry=118.0, stop_loss=105.0, target=145.0)
    assert isinstance(exp, TradeExplanation)
    assert exp.symbol == "NIFTY"
    assert "₹118.00" in exp.why_entry
    assert "₹105.00" in exp.why_stop
    assert "₹145.00" in exp.why_target
    assert exp.win_probability == 78.5


def test_ai_trading_coach_compare_setup():
    res = AITradingCoachEngine.compare_setup("NIFTY")
    assert isinstance(res, SetupMatchResult)
    assert res.matched_count == 1000
    assert res.historical_win_rate == 76.4
    assert res.confidence_edge == "STRONG_QUANT_EDGE"


def test_ai_trading_coach_grade_trade():
    lessons = AITradingCoachEngine.grade_trade(risk_compliant=True, followed_plan=True, win_rate=80.0)
    assert isinstance(lessons, LessonsLearned)
    assert lessons.trade_grade == "A+"

    lessons_b = AITradingCoachEngine.grade_trade(risk_compliant=True, followed_plan=False)
    assert lessons_b.trade_grade == "B"

    lessons_d = AITradingCoachEngine.grade_trade(risk_compliant=False, followed_plan=False)
    assert lessons_d.trade_grade == "D"


def test_performance_auditor_reports():
    daily = PerformanceAuditor.generate_daily_report()
    assert isinstance(daily, AuditReport)
    assert daily.period_type == "DAILY"
    assert daily.psychology_score == 92.0

    weekly = PerformanceAuditor.generate_weekly_report()
    assert weekly.period_type == "WEEKLY"
    assert weekly.net_pnl == 18400.0

    monthly = PerformanceAuditor.generate_monthly_report()
    assert monthly.period_type == "MONTHLY"
    assert monthly.risk_score == 97.0
