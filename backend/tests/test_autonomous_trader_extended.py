"""Extended unit tests for AutonomousPaperTrader state transitions and active trade management."""

from datetime import datetime

import pytest

from app.analytics.multi_agent.decision import AITradeDecision
from app.paper.autonomous_trader import ActiveManagedTrade, AutonomousPaperTrader, TimelineEvent
from app.paper.state_machine import TradeState, TradeStateMachine


def test_timeline_event_dataclass():
    event = TimelineEvent(timestamp=datetime.now(), category="ORDER", message="Order filled")
    assert event.category == "ORDER"
    assert "filled" in event.message


def test_autonomous_trader_add_timeline_event():
    trader = AutonomousPaperTrader()
    initial_count = len(trader.ai_timeline)
    trader.add_timeline_event("RISK", "Risk budget clear for NIFTY trade")
    assert len(trader.ai_timeline) == initial_count + 1
    assert trader.ai_timeline[-1].category == "RISK"


def test_active_managed_trade_dataclass():
    sm = TradeStateMachine("TRADE_999", TradeState.WAITING)
    decision = AITradeDecision(
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
    trade = ActiveManagedTrade(
        trade_id="TRADE_999",
        symbol="NIFTY",
        contract_symbol="NIFTY 24900 CE",
        entry_price=118.0,
        current_price=118.0,
        quantity=25,
        stop_loss=105.0,
        target1=135.0,
        target2=155.0,
        target3=180.0,
        state_machine=sm,
        decision=decision,
    )
    assert trade.trade_id == "TRADE_999"
    assert trade.quantity == 25
    assert trade.stop_loss == 105.0


def test_autonomous_trader_manage_open_trades_trailing():
    trader = AutonomousPaperTrader()
    sm = TradeStateMachine("NIFTY_24900_CE", TradeState.ENTERED)
    decision = AITradeDecision(
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
    trade = ActiveManagedTrade(
        trade_id="NIFTY_24900_CE",
        symbol="NIFTY",
        contract_symbol="NIFTY 24900 CE",
        entry_price=118.0,
        current_price=138.0,  # Target 1 hit
        quantity=25,
        stop_loss=105.0,
        target1=135.0,
        target2=155.0,
        target3=180.0,
        state_machine=sm,
        decision=decision,
    )
    trader.active_trades["NIFTY_24900_CE"] = trade
    trader.manage_open_trades()

    # Should transition to PARTIAL_EXIT -> TRAILING and move SL to entry 118.0
    assert trade.stop_loss == 118.0
    assert trade.state_machine.current_state in (TradeState.TRAILING, TradeState.PARTIAL_EXIT)


def test_autonomous_trader_manage_open_trades_stop_loss_exit():
    trader = AutonomousPaperTrader()
    sm = TradeStateMachine("BANKNIFTY_55000_PE", TradeState.ENTERED)
    decision = AITradeDecision(
        symbol="BANKNIFTY",
        expiry="Thursday Weekly",
        strike=55000.0,
        option_type="PE",
        action="BUY",
        entry=115.0,
        stop_loss=102.0,
        target1=132.0,
        target2=150.0,
        target3=175.0,
        confidence=85.0,
        expected_hold_time="15-30 mins",
        risk_reward="1:2.5",
    )
    trade = ActiveManagedTrade(
        trade_id="BANKNIFTY_55000_PE",
        symbol="BANKNIFTY",
        contract_symbol="BANKNIFTY 55000 PE",
        entry_price=115.0,
        current_price=100.0,  # Below stop loss
        quantity=15,
        stop_loss=102.0,
        target1=132.0,
        target2=150.0,
        target3=175.0,
        state_machine=sm,
        decision=decision,
    )
    trader.active_trades["BANKNIFTY_55000_PE"] = trade
    trader.manage_open_trades()

    # Trade should be exited and removed from active_trades
    assert "BANKNIFTY_55000_PE" not in trader.active_trades
