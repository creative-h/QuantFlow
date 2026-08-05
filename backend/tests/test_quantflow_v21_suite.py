"""QuantFlow v2.1 AI Trading Desk & Professional Intelligence Test Suite."""

from datetime import datetime
import pandas as pd
import pytest

from app.analytics.ai_coach import AICoach, AICoachAdvice
from app.analytics.market_health import MarketHealthItem, MarketHealthMonitor, MarketHealthOverview
from app.analytics.multi_agent.debate import AIDebateEngine, AIDebateSession, DebateParticipant
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.analytics.multi_agent.scoreboard import ScoreboardConsensus, StrategyScoreboard, StrategyVote
from app.models.dataclasses import Candle


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
        agent_opinions=[
            AgentOpinion("TrendAgent", 92.0, 90.0, "EMA trend strong", "BULLISH"),
            AgentOpinion("MomentumAgent", 61.0, 60.0, "Red candle pullback", "NEUTRAL"),
            AgentOpinion("VWAPAgent", 90.0, 88.0, "Spot above VWAP", "BULLISH"),
            AgentOpinion("OptionsOIAnalyzer", 88.0, 85.0, "PCR 1.18 bullish", "BULLISH"),
            AgentOpinion("RiskAgent", 95.0, 95.0, "Risk approved", "BULLISH"),
        ],
    )


def test_ai_debate_engine_create_debate(sample_decision):
    debate = AIDebateEngine.create_debate(sample_decision)
    assert isinstance(debate, AIDebateSession)
    assert debate.consensus_action == "BUY"
    assert debate.consensus_confidence == 88.0
    assert len(debate.participants) == 5
    assert debate.participants[0].name == "TrendAgent"
    assert debate.participants[0].vote == "BUY"


def test_strategy_scoreboard_evaluation():
    candle = Candle(datetime.now(), 24900, 24950, 24880, 24920, 2500)
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    df = pd.DataFrame(
        {"open": [24900]*20, "high": [24950]*20, "low": [24880]*20, "close": [24920]*20, "volume": [2500]*20},
        index=dates,
    )
    sb = StrategyScoreboard.evaluate_scoreboard("NIFTY", candle, df)
    assert isinstance(sb, ScoreboardConsensus)
    assert len(sb.votes) >= 5
    assert sb.buy_count + sb.sell_count + sb.wait_count == len(sb.votes)


def test_market_health_monitor():
    overview = MarketHealthMonitor.get_market_health()
    assert isinstance(overview, MarketHealthOverview)
    assert len(overview.items) == 6
    assert overview.market_breadth_pct == 82.0
    assert overview.items[0].name == "NIFTY"
    assert "★" in overview.items[0].stars


def test_ai_coach_advice_generation(sample_decision):
    advice = AICoach.generate_advice(sample_decision)
    assert isinstance(advice, AICoachAdvice)
    assert advice.symbol == "NIFTY"
    assert "BUY NIFTY 24900 CE" in advice.recommendation
    assert "BUY NOW" in advice.action_answer
    assert advice.why_explanation != ""
    assert "Pro Tip" in advice.coach_tip


def test_ai_coach_advice_wait(sample_decision):
    sample_decision.action = "WAIT"
    sample_decision.confidence = 60.0
    advice = AICoach.generate_advice(sample_decision)
    assert advice.recommendation == "WAIT / WATCH NIFTY"
    assert "WAIT FOR NEXT CANDLE CLOSE" in advice.action_answer


def test_v21_suite_debate_participant_dataclass():
    p = AIDebateEngine.create_debate(
        AITradeDecision("BANKNIFTY", "Weekly", 55000.0, "PE", "BUY", 115.0, 102.0, 132.0, 150.0, 175.0, 85.0, "15m", "1:2.5")
    )
    assert p.consensus_action == "BUY"


def test_v21_suite_market_health_item_dataclass():
    item = MarketHealthItem("SENSEX", "Bullish", "★★★★☆", 4, "Strong macro alignment")
    assert item.name == "SENSEX"
    assert item.score == 4


def test_v21_suite_strategy_vote_dataclass():
    v = StrategyVote("EMA", "BUY", 92.0, "EMA fast > slow")
    assert v.strategy_name == "EMA"
    assert v.vote == "BUY"


def test_v21_suite_scoreboard_consensus_alignment_score():
    c = ScoreboardConsensus(datetime.now(), [], 3, 1, 2, "BUY", 50.0)
    assert c.consensus_recommendation == "BUY"
    assert c.buy_count == 3


def test_v21_suite_ai_coach_advice_timestamp():
    adv = AICoachAdvice(datetime.now(), "NIFTY", "BUY", "BUY NOW", "Why test", "Risk test", "Tip test")
    assert adv.symbol == "NIFTY"
    assert isinstance(adv.timestamp, datetime)
