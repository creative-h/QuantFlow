"""QuantFlow v2.0 Real-Time Automation Comprehensive Test Suite."""

from datetime import datetime
from pathlib import Path
import yaml
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
from app.marketdata.candle_builder import CandleBuilder
from app.marketdata.live_feed import KiteLiveFeedManager, Tick
from app.models.dataclasses import Candle
from app.paper.autonomous_trader import ActiveManagedTrade, AutonomousPaperTrader
from app.paper.journal.pro_journal import ProJournalEntry, ProTradeJournal
from app.paper.state_machine import TradeState, TradeStateMachine


def test_v2_suite_live_feed_tick_cache():
    feed = KiteLiveFeedManager(symbols=["NIFTY"])
    feed.start()
    import time
    time.sleep(1.0)
    tick = feed.get_latest_tick("NIFTY")
    assert tick is not None
    assert tick.price > 0.0
    feed.stop()


def test_v2_suite_candle_builder_1m_3m_5m_15m():
    builder = CandleBuilder()
    now = datetime(2024, 1, 1, 10, 0, 0)
    builder.process_tick(Tick("NIFTY", 24900.0, 100, now))
    assert "1m" in builder._current_candles["NIFTY"]
    assert "3m" in builder._current_candles["NIFTY"]
    assert "5m" in builder._current_candles["NIFTY"]
    assert "15m" in builder._current_candles["NIFTY"]


def test_v2_suite_agent_opinion_dataclass():
    op = AgentOpinion("TestAgent", 90.0, 85.0, "Test reason", "BULLISH")
    assert op.agent_name == "TestAgent"
    assert op.score == 90.0
    assert op.recommendation == "BULLISH"


def test_v2_suite_ai_trade_decision_dataclass():
    dec = AITradeDecision(
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
    )
    assert dec.symbol == "NIFTY"
    assert dec.strike == 24900.0
    assert dec.action == "BUY"


def test_v2_suite_state_machine_8_states():
    sm = TradeStateMachine("T_1", TradeState.WAITING)
    assert sm.current_state == TradeState.WAITING
    assert sm.transition_to(TradeState.WATCHLIST)
    assert sm.transition_to(TradeState.READY)
    assert sm.transition_to(TradeState.ENTERED)
    assert sm.transition_to(TradeState.PARTIAL_EXIT)
    assert sm.transition_to(TradeState.TRAILING)
    assert sm.transition_to(TradeState.EXITED)
    assert sm.current_state == TradeState.EXITED


def test_v2_suite_autonomous_trader_scan():
    trader = AutonomousPaperTrader()
    trader.scan_and_execute()
    assert isinstance(trader.ai_timeline, list)


def test_v2_suite_pro_journal_exports():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        j = ProTradeJournal(journal_file=Path(tmp) / "j.json")
        dec = AITradeDecision("NIFTY", "Thursday Weekly", 24900.0, "CE", "BUY", 118.0, 105.0, 135.0, 155.0, 180.0, 88.0, "15-30 mins", "1:2.7")
        j.log_trade_entry(ProJournalEntry("TR1", "NIFTY", "NIFTY 24900 CE", datetime.now(), datetime.now(), 118.0, 135.0, 25, 425.0, 600.0, "Target Hit", dec))
        csv_file = j.export_csv(Path(tmp) / "j.csv")
        assert csv_file.exists()


def test_v2_suite_config_strategies_yaml():
    p = Path(__file__).parent.parent / "config" / "strategies.yaml"
    with open(p, "r") as f:
        cfg = yaml.safe_load(f)
    assert "active_strategies" in cfg


def test_v2_suite_config_risk_yaml():
    p = Path(__file__).parent.parent / "config" / "risk.yaml"
    with open(p, "r") as f:
        cfg = yaml.safe_load(f)
    assert cfg["risk_parameters"]["max_position_size_pct"] == 10.0


def test_v2_suite_config_ai_yaml():
    p = Path(__file__).parent.parent / "config" / "ai.yaml"
    with open(p, "r") as f:
        cfg = yaml.safe_load(f)
    assert cfg["ai_consensus"]["min_confidence_threshold"] == 75.0


def test_v2_suite_config_market_yaml():
    p = Path(__file__).parent.parent / "config" / "market.yaml"
    with open(p, "r") as f:
        cfg = yaml.safe_load(f)
    assert "NIFTY" in cfg["market_feed"]["primary_indices"]


def test_v2_suite_config_paper_yaml():
    p = Path(__file__).parent.parent / "config" / "paper.yaml"
    with open(p, "r") as f:
        cfg = yaml.safe_load(f)
    assert cfg["paper_trading"]["initial_cash"] == 100000.0


def test_v2_suite_trend_agent_direct_call():
    c = Candle(datetime.now(), 24900, 24950, 24880, 24920, 1000)
    op = TrendAgent().evaluate("NIFTY", c, None)
    assert op.agent_name == "TrendAgent"


def test_v2_suite_momentum_agent_direct_call():
    c = Candle(datetime.now(), 24900, 24950, 24880, 24920, 1000)
    op = MomentumAgent().evaluate("NIFTY", c, None)
    assert op.agent_name == "MomentumAgent"


def test_v2_suite_vwap_agent_direct_call():
    c = Candle(datetime.now(), 24900, 24950, 24880, 24920, 1000)
    op = VWAPAgent().evaluate("NIFTY", c, 24900.0)
    assert op.agent_name == "VWAPAgent"


def test_v2_suite_risk_agent_direct_call():
    c = Candle(datetime.now(), 24900, 24950, 24880, 24920, 1000)
    op = RiskAgent().evaluate("NIFTY", c)
    assert op.agent_name == "RiskAgent"


def test_v2_suite_regime_agent_direct_call():
    op = MarketRegimeAgent().evaluate(None)
    assert op.agent_name == "MarketRegimeAgent"


def test_v2_suite_news_agent_direct_call():
    op = NewsSentimentAgent().evaluate("NIFTY")
    assert op.agent_name == "NewsSentimentAgent"


def test_v2_suite_state_machine_rejected_transition():
    sm = TradeStateMachine("T_REJ", TradeState.WAITING)
    assert sm.transition_to(TradeState.REJECTED, reason="Drawdown limit hit")
    assert sm.current_state == TradeState.REJECTED


def test_v2_suite_state_machine_watchlist_to_ready():
    sm = TradeStateMachine("T_READY", TradeState.WAITING)
    sm.transition_to(TradeState.WATCHLIST)
    assert sm.transition_to(TradeState.READY)
    assert sm.current_state == TradeState.READY


def test_v2_suite_state_machine_entered_to_exited():
    sm = TradeStateMachine("T_EXIT", TradeState.ENTERED)
    assert sm.transition_to(TradeState.EXITED, reason="Manual exit")
    assert sm.current_state == TradeState.EXITED


def test_v2_suite_autonomous_trader_stop():
    trader = AutonomousPaperTrader()
    trader.stop()
    assert not trader.is_auto_trading


def test_v2_suite_decision_coordinator_custom_threshold():
    coordinator = DecisionCoordinator(min_confidence_threshold=80.0)
    assert coordinator.min_confidence_threshold == 80.0


def test_v2_suite_tick_dataclass_defaults():
    t = Tick("BANKNIFTY", 55000.0, 500)
    assert t.symbol == "BANKNIFTY"
    assert t.price == 55000.0
    assert t.volume == 500
