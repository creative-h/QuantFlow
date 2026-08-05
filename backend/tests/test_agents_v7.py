"""Unit tests for QuantFlow v7.0 Multi-Agent AI Decision Engine and Specialist Agents."""

from datetime import datetime
import pandas as pd
import pytest

from app.agents.decision import AgentDecision
from app.agents.decision_manager import DecisionManager, MultiAgentConsensus
from app.agents.momentum_agent import MomentumAgent
from app.agents.oi_agent import OIAgent
from app.agents.option_chain_agent import OptionChainAgent
from app.agents.pcr_agent import PCRAgent
from app.agents.price_action_agent import PriceActionAgent
from app.agents.risk_agent import RiskAgent
from app.agents.trend_agent import TrendAgent
from app.agents.volatility_agent import VolatilityAgent
from app.agents.volume_agent import VolumeAgent
from app.agents.vwap_agent import VWAPAgent
from app.models.dataclasses import Candle


@pytest.fixture
def sample_candle() -> Candle:
    c = Candle(datetime.now(), 24900.0, 24950.0, 24880.0, 24920.0, 2500)
    c.symbol = "NIFTY"
    return c


@pytest.fixture
def sample_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "open": [24900.0] * 30,
            "high": [24950.0] * 30,
            "low": [24880.0] * 30,
            "close": [24900.0 + i * 5.0 for i in range(30)],
            "volume": [2500] * 30,
        },
        index=dates,
    )


def test_agent_decision_dataclass():
    dec = AgentDecision("TestAgent", "BUY", 88.5, "Test reason", {"val": 10})
    assert dec.agent_name == "TestAgent"
    assert dec.signal == "BUY"
    assert dec.confidence == 88.5


def test_trend_agent_evaluation(sample_candle, sample_df):
    agent = TrendAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "TrendAgent"
    assert dec.signal in ("BUY", "SELL", "WAIT")


def test_momentum_agent_evaluation(sample_candle, sample_df):
    agent = MomentumAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "MomentumAgent"


def test_vwap_agent_evaluation(sample_candle, sample_df):
    agent = VWAPAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "VWAPAgent"


def test_volume_agent_evaluation(sample_candle, sample_df):
    agent = VolumeAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "VolumeAgent"


def test_price_action_agent_evaluation(sample_candle, sample_df):
    agent = PriceActionAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "PriceActionAgent"


def test_option_chain_agent_evaluation(sample_candle, sample_df):
    agent = OptionChainAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "OptionChainAgent"


def test_oi_agent_evaluation(sample_candle, sample_df):
    agent = OIAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "OIAgent"


def test_pcr_agent_evaluation(sample_candle, sample_df):
    agent = PCRAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "PCRAgent"


def test_volatility_agent_evaluation(sample_candle, sample_df):
    agent = VolatilityAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "VolatilityAgent"


def test_risk_agent_evaluation(sample_candle, sample_df):
    agent = RiskAgent()
    dec = agent.evaluate(sample_candle, sample_df)
    assert isinstance(dec, AgentDecision)
    assert dec.agent_name == "RiskAgent"


def test_decision_manager_consensus_evaluation(sample_candle, sample_df):
    mgr = DecisionManager()
    consensus = mgr.evaluate_consensus(sample_candle, sample_df)
    assert isinstance(consensus, MultiAgentConsensus)
    assert consensus.final_signal in ("BUY", "SELL", "WAIT")
    assert len(consensus.agent_decisions) == 10
    assert "BUY" in consensus.voting_distribution
