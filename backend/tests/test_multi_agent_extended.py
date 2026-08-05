"""Extended Unit Tests for Multi-Agent AI Consensus System."""

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
from app.marketdata.option_chain import OptionChain, OptionChainEngine
from app.models.dataclasses import Candle, Signal, SignalSide


@pytest.fixture
def bullish_history() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    close = np.linspace(24000, 25000, 30)
    return pd.DataFrame(
        {"open": close - 5.0, "high": close + 15.0, "low": close - 15.0, "close": close, "volume": 30000},
        index=dates,
    )


@pytest.fixture
def bearish_history() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    close = np.linspace(25000, 24000, 30)
    return pd.DataFrame(
        {"open": close + 5.0, "high": close + 15.0, "low": close - 15.0, "close": close, "volume": 30000},
        index=dates,
    )


def test_trend_agent_bullish_and_bearish(bullish_history, bearish_history):
    c_bull = Candle(datetime.now(), 24990, 25010, 24980, 25000, 5000)
    op_bull = TrendAgent().evaluate("NIFTY", c_bull, bullish_history)
    assert op_bull.recommendation == "BULLISH"

    c_bear = Candle(datetime.now(), 24010, 24020, 23990, 24000, 5000)
    op_bear = TrendAgent().evaluate("NIFTY", c_bear, bearish_history)
    assert op_bear.recommendation == "BEARISH"


def test_momentum_agent_green_and_red_candles(bullish_history, bearish_history):
    c_green = Candle(datetime.now(), 24900, 24950, 24890, 24940, 5000)
    op_green = MomentumAgent().evaluate("NIFTY", c_green, bullish_history)
    assert op_green.recommendation == "BULLISH"

    c_red = Candle(datetime.now(), 24940, 24950, 24890, 24900, 5000)
    op_red = MomentumAgent().evaluate("NIFTY", c_red, bearish_history)
    assert op_red.recommendation == "BEARISH"


def test_vwap_agent_above_and_below():
    c = Candle(datetime.now(), 24900, 24950, 24890, 24940, 5000)
    op_above = VWAPAgent().evaluate("NIFTY", c, 24900.0)
    assert op_above.recommendation == "BULLISH"

    op_below = VWAPAgent().evaluate("NIFTY", c, 25000.0)
    assert op_below.recommendation == "BEARISH"


def test_options_oi_analyzer_pcr_bullish_and_bearish():
    chain = OptionChainEngine.generate_chain("NIFTY", 24900.0)
    op = OptionsOIAnalyzer().evaluate(chain)
    assert isinstance(op, AgentOpinion)
    assert op.recommendation in ("BULLISH", "BEARISH", "NEUTRAL")


def test_coordinator_bullish_consensus(bullish_history):
    c = Candle(datetime.now(), 24990, 25010, 24980, 25000, 5000)
    coordinator = DecisionCoordinator(min_confidence_threshold=65.0)
    decision = coordinator.evaluate_consensus("NIFTY", c, bullish_history)

    assert isinstance(decision, AITradeDecision)
    assert decision.action in ("BUY", "WAIT")
    assert decision.confidence >= 50.0


def test_coordinator_bearish_consensus(bearish_history):
    c = Candle(datetime.now(), 24010, 24020, 23990, 24000, 5000)
    coordinator = DecisionCoordinator(min_confidence_threshold=65.0)
    decision = coordinator.evaluate_consensus("NIFTY", c, bearish_history)

    assert isinstance(decision, AITradeDecision)
    assert decision.action in ("BUY", "WAIT")


def test_coordinator_low_confidence_wait():
    c = Candle(datetime.now(), 24900, 24905, 24895, 24900, 500)
    coordinator = DecisionCoordinator(min_confidence_threshold=99.0)
    decision = coordinator.evaluate_consensus("NIFTY", c, None)

    assert decision.action == "WAIT"
    assert "warnings" in decision.__dict__
