"""Unit tests for QuantFlow v11.0 Autonomous Learning Engine & Research Lab."""

import pytest

from app.research.agent_scorecard import AgentScorecardEngine
from app.research.audit_reports import AIDailyMonthlyReporter
from app.research.feature_importance import FeatureImportanceAnalyzer
from app.research.parameter_evolution import AutoParameterEvolution
from app.research.regime_analyzer import MarketRegimeAnalyzer
from app.research.self_learning import SelfLearningLoop
from app.research.strategy_scorer import StrategyScoreEngine
from app.research.trade_dataset import TradeDatasetBuilder, TradeRecord


def test_trade_dataset_builder(tmp_path):
    builder = TradeDatasetBuilder(storage_dir=str(tmp_path))
    df = builder.to_dataframe()
    assert not df.empty
    assert len(df) >= 20

    csv_p = builder.export_csv()
    assert csv_p.exists()

    parq_p = builder.export_parquet()
    assert parq_p.exists()

    sql_p = builder.export_sqlite()
    assert sql_p.exists()


def test_feature_importance_analyzer():
    builder = TradeDatasetBuilder()
    df = builder.to_dataframe()
    importance = FeatureImportanceAnalyzer.analyze_feature_importance(df)
    assert isinstance(importance, dict)
    assert "vwap" in importance or "ema20" in importance

    ranks = FeatureImportanceAnalyzer.get_top_and_worst_indicators(df)
    assert len(ranks["top_indicators"]) == 3
    assert len(ranks["worst_indicators"]) == 3


def test_strategy_score_engine():
    leaderboard = StrategyScoreEngine.evaluate_strategies()
    assert len(leaderboard) >= 5
    assert leaderboard[0].composite_score >= leaderboard[1].composite_score


def test_agent_scorecard_engine():
    scorecards = AgentScorecardEngine.evaluate_agents()
    assert len(scorecards) == 10
    assert scorecards[0].contribution_score >= scorecards[1].contribution_score


def test_market_regime_analyzer():
    regimes = MarketRegimeAnalyzer.analyze_regimes()
    assert len(regimes) == 5
    assert any(r.regime_name == "BULL_TREND" for r in regimes)


def test_auto_parameter_evolution():
    evo = AutoParameterEvolution()
    assert len(evo.version_history) >= 2

    new_v = evo.optimize_parameters("Supertrend")
    assert new_v.indicator_name == "Supertrend"
    assert len(evo.version_history) >= 3


def test_ai_daily_monthly_reporter(tmp_path):
    daily = AIDailyMonthlyReporter.generate_daily_review()
    assert daily.net_pnl == 4850.0

    html_p = AIDailyMonthlyReporter.export_monthly_html_report(output_dir=str(tmp_path))
    assert html_p.exists()


def test_self_learning_loop():
    sll = SelfLearningLoop()
    state = sll.update_learning_state(trade_pnl=450.0, winning_trade=True)
    assert state.updated_agent_weights["OptionChainAgent"] > 1.0
    assert state.top_strategy == "MultiAgentConsensus"
