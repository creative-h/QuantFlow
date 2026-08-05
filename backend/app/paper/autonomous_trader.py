"""Autonomous Paper Trader managing continuous AI scanning, order execution, and trailing stops."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import threading
import time
from typing import Dict, List, Optional

from loguru import logger

from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.decision import AITradeDecision
from app.brokers.paper_broker import PaperBroker
from app.marketdata.live_feed import KiteLiveFeedManager, Tick
from app.models.dataclasses import Candle
from app.models.trading import Order, OrderRequest, OrderType, Side
from app.paper.state_machine import TradeState, TradeStateMachine


@dataclass
class TimelineEvent:
    """Dataclass storing live AI commentary timeline log."""

    timestamp: datetime
    category: str  # "SCANNING", "SIGNAL", "RISK", "ORDER", "TRAILING", "EXIT"
    message: str


@dataclass
class ActiveManagedTrade:
    """Dataclass tracking an active autonomous option trade."""

    trade_id: str
    symbol: str
    contract_symbol: str
    entry_price: float
    current_price: float
    quantity: int
    stop_loss: float
    target1: float
    target2: float
    target3: float
    state_machine: TradeStateMachine
    decision: AITradeDecision
    unrealized_pnl: float = 0.0
    highest_price: float = 0.0


class AutonomousPaperTrader:
    """Fully automated paper trading engine driven by Multi-Agent AI consensus."""

    def __init__(
        self,
        broker: Optional[PaperBroker] = None,
        live_feed: Optional[KiteLiveFeedManager] = None,
        coordinator: Optional[DecisionCoordinator] = None,
        min_confidence: float = 75.0,
    ) -> None:
        self.broker = broker or PaperBroker(initial_cash=100000.0)
        self.live_feed = live_feed or KiteLiveFeedManager()
        self.coordinator = coordinator or DecisionCoordinator(min_confidence_threshold=min_confidence)
        self.min_confidence = min_confidence
        self.is_auto_trading = False
        self.active_trades: Dict[str, ActiveManagedTrade] = {}
        self.ai_timeline: List[TimelineEvent] = []
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

        self.add_timeline_event("SCANNING", "Autonomous Paper Trader initialized; ready for real-time scanning")

    def add_timeline_event(self, category: str, message: str) -> None:
        """Add live event log to AI commentary timeline."""
        event = TimelineEvent(timestamp=datetime.now(), category=category, message=message)
        with self._lock:
            self.ai_timeline.append(event)
            # Keep latest 100 events
            if len(self.ai_timeline) > 100:
                self.ai_timeline.pop(0)
        logger.info("AI TIMELINE [{}]: {}", category, message)

    def start(self) -> None:
        """Start autonomous trading scanner and trade manager thread."""
        if self.is_auto_trading:
            logger.warning("AutonomousPaperTrader is already running")
            return

        self.is_auto_trading = True
        self.live_feed.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.add_timeline_event("SCANNING", "Autonomous trading loop started; scanning Indian index feeds")

    def stop(self) -> None:
        """Stop autonomous trading engine."""
        self.is_auto_trading = False
        self.live_feed.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.add_timeline_event("SCANNING", "Autonomous trading engine stopped")

    def _run_loop(self) -> None:
        """Continuous background scan loop."""
        while self.is_auto_trading:
            try:
                self.scan_and_execute()
                self.manage_open_trades()
                time.sleep(2.0)
            except Exception as err:
                logger.error("Error in AutonomousPaperTrader loop: {}", str(err))
                time.sleep(2.0)

    def scan_and_execute(self) -> None:
        """Scan ticks, evaluate multi-agent consensus, and place paper orders automatically."""
        all_ticks = self.live_feed.get_all_ticks()
        for symbol, tick in all_ticks.items():
            # Build current candle
            candle_obj = Candle(
                timestamp=tick.timestamp,
                open=tick.open or tick.price,
                high=tick.high or tick.price,
                low=tick.low or tick.price,
                close=tick.price,
                volume=tick.volume,
            )

            # Evaluate Multi-Agent AI Consensus
            decision = self.coordinator.evaluate_consensus(symbol, candle_obj, history=None)

            if decision.action == "BUY" and decision.confidence >= self.min_confidence:
                trade_key = f"{decision.symbol}_{decision.strike}_{decision.option_type}"

                if trade_key not in self.active_trades and len(self.active_trades) < 5:
                    self.add_timeline_event(
                        "SIGNAL",
                        f"AI Consensus BUY signal confirmed for {decision.contract_symbol} with {decision.confidence}% confidence",
                    )
                    self._execute_autonomous_trade(trade_key, decision, tick.price)

    def _execute_autonomous_trade(self, trade_key: str, decision: AITradeDecision, spot_price: float) -> None:
        """Execute paper order, create state machine, and log transition to ENTERED."""
        sm = TradeStateMachine(trade_id=trade_key, initial_state=TradeState.WAITING)
        sm.transition_to(TradeState.WATCHLIST, reason="Confidence threshold satisfied")
        sm.transition_to(TradeState.READY, reason="Pre-trade risk limits clear")

        req = OrderRequest(
            symbol=decision.symbol,
            quantity=25,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=Decimal(str(decision.entry)),
        )

        try:
            # Submit to paper broker synchronously using event loop
            loop = asyncio.new_event_loop()
            executed_order = loop.run_until_complete(self.broker.place_order(req))
            loop.close()

            if executed_order.status.value in ("FILLED", "OPEN"):
                sm.transition_to(TradeState.ENTERED, reason=f"Market order filled @ ₹{decision.entry}")
                managed_trade = ActiveManagedTrade(
                    trade_id=trade_key,
                    symbol=decision.symbol,
                    contract_symbol=decision.contract_symbol,
                    entry_price=decision.entry,
                    current_price=decision.entry,
                    quantity=25,
                    stop_loss=decision.stop_loss,
                    target1=decision.target1,
                    target2=decision.target2,
                    target3=decision.target3,
                    state_machine=sm,
                    decision=decision,
                    highest_price=decision.entry,
                )

                with self._lock:
                    self.active_trades[trade_key] = managed_trade

                self.add_timeline_event(
                    "ORDER",
                    f"EXECUTED: Autonomous BUY {decision.contract_symbol} Qty 25 @ ₹{decision.entry} (SL: ₹{decision.stop_loss}, Target: ₹{decision.target1})",
                )
            else:
                sm.transition_to(TradeState.REJECTED, reason=f"Order status: {executed_order.status.value}")
        except Exception as err:
            logger.error("Failed to execute autonomous trade: {}", str(err))
            sm.transition_to(TradeState.REJECTED, reason=str(err))

    def manage_open_trades(self) -> None:
        """Monitor open positions, update trailing stops, execute partial/target/stop-loss exits."""
        with self._lock:
            active_keys = list(self.active_trades.keys())

        for key in active_keys:
            with self._lock:
                trade = self.active_trades.get(key)

            if not trade:
                continue

            # Update current tick price if available from live feed
            tick = self.live_feed.get_latest_tick(trade.symbol)
            if tick and tick.open > 0:
                price_delta = (tick.price - tick.open) * 0.5
                curr_premium = round(max(10.0, trade.entry_price + price_delta), 2)
            else:
                curr_premium = trade.current_price

            trade.current_price = curr_premium
            trade.highest_price = max(trade.highest_price, curr_premium)
            trade.unrealized_pnl = round((curr_premium - trade.entry_price) * trade.quantity, 2)

            # Check Exits
            sm = trade.state_machine
            if curr_premium <= trade.stop_loss:
                sm.transition_to(TradeState.EXITED, reason=f"Stop Loss breached @ ₹{curr_premium}")
                self.add_timeline_event("EXIT", f"STOP LOSS EXITED: {trade.contract_symbol} @ ₹{curr_premium} (PnL: ₹{trade.unrealized_pnl})")
                with self._lock:
                    del self.active_trades[key]

            elif curr_premium >= trade.target1 and sm.current_state == TradeState.ENTERED:
                sm.transition_to(TradeState.PARTIAL_EXIT, reason=f"Target 1 reached @ ₹{curr_premium}")
                # Move SL to Entry (Break-even)
                trade.stop_loss = trade.entry_price
                sm.transition_to(TradeState.TRAILING, reason="Trailing stop activated to break-even")
                self.add_timeline_event(
                    "TRAILING",
                    f"TARGET 1 HIT: {trade.contract_symbol} @ ₹{curr_premium}! Trailing stop moved to break-even ₹{trade.stop_loss}",
                )

            elif curr_premium >= trade.target3:
                sm.transition_to(TradeState.EXITED, reason=f"Target 3 reached @ ₹{curr_premium}")
                self.add_timeline_event("EXIT", f"FULL TARGET 3 EXITED: {trade.contract_symbol} @ ₹{curr_premium} (PnL: +₹{trade.unrealized_pnl})")
                with self._lock:
                    del self.active_trades[key]
