"""Unit tests for Multi-Agent AI System and DecisionCoordinator."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from app.analytics.multi_agent.agents import (
    MarketRegimeAgent,
    MomentumAgent,
    NewsSentimentAgent,
    OptionsOIAnalyzer,
    RiskAgent,
    TrendAgent,
    VWAPAgent,
)
from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.models.dataclasses import Candle


@pytest.fixture
def sample_candle() -> Candle:
    return Candle(
        timestamp=datetime.now(),
        open=24900.0,
        high=24950.0,
        low=24880.0,
        close=24915.20,
        volume=2500,
    )


@pytest.fixture
def sample_history() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    close = 24900.0 + np.cumsum(np.random.randn(30) * 10.0)
    return pd.DataFrame(
        {"open": close - 5.0, "high": close + 15.0, "low": close - 15.0, "close": close, "volume": 30000},
        index=dates,
    )


def test_individual_sub_agents(sample_candle, sample_history):
    trend_op = TrendAgent().evaluate("NIFTY", sample_candle, sample_history)
    assert isinstance(trend_op, AgentOpinion)
    assert trend_op.agent_name == "TrendAgent"
    assert 0.0 <= trend_op.score <= 100.0

    mom_op = MomentumAgent().evaluate("NIFTY", sample_candle, sample_history)
    assert isinstance(mom_op, AgentOpinion)

    vwap_op = VWAPAgent().evaluate("NIFTY", sample_candle, 24900.0)
    assert isinstance(vwap_op, AgentOpinion)

    oi_op = OptionsOIAnalyzer().evaluate(None)
    assert isinstance(oi_op, AgentOpinion)

    risk_op = RiskAgent().evaluate("NIFTY", sample_candle)
    assert isinstance(risk_op, AgentOpinion)

    regime_op = MarketRegimeAgent().evaluate(sample_history)
    assert isinstance(regime_op, AgentOpinion)

    news_op = NewsSentimentAgent().evaluate("NIFTY")
    assert isinstance(news_op, AgentOpinion)


def test_decision_coordinator_consensus(sample_candle, sample_history):
    coordinator = DecisionCoordinator(min_confidence_threshold=70.0)
    decision = coordinator.evaluate_consensus("NIFTY", sample_candle, sample_history)

    assert isinstance(decision, AITradeDecision)
    assert decision.symbol == "NIFTY"
    assert decision.action in ("BUY", "WAIT")
    assert decision.confidence >= 50.0
    assert len(decision.reasons) > 0
    assert len(decision.agent_opinions) == 7
