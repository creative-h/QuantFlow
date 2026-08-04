"""Real-time Live Paper Trading Engine with market poller, automated execution, alerts, and recovery."""

import asyncio
import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.brokers.paper_broker import PaperBroker
from app.marketdata.base import MarketDataProvider
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.models.dataclasses import Candle
from app.models.trading import Order, OrderRequest, OrderType, Side
from app.services.alert_engine import AlertEngine, AlertLevel
from app.strategies.base import Strategy
from app.strategies.registry import StrategyRegistry


class LivePaperEngineState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


@dataclass
class LivePaperSessionConfig:
    """Configuration payload for live paper trading session."""

    symbols: List[str]
    strategy_names: List[str]
    poll_interval_seconds: int = 5
    initial_cash: float = 100000.0
    auto_eod_report: bool = True


class LivePaperEngine:
    """Engine managing real-time market polling, signal generation, paper execution, and recovery."""

    def __init__(
        self,
        data_provider: Optional[MarketDataProvider] = None,
        alert_engine: Optional[AlertEngine] = None,
        session_file: Optional[Path] = None,
    ) -> None:
        self.data_provider = data_provider or YahooFinanceProvider()
        self.alert_engine = alert_engine or AlertEngine()
        self.state = LivePaperEngineState.STOPPED
        self.config: Optional[LivePaperSessionConfig] = None
        self.broker: Optional[PaperBroker] = None
        self.active_strategies: Dict[str, Strategy] = {}
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[threading.Thread] = None
        self._market_history: Dict[str, pd.DataFrame] = {}

        if session_file is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.session_file = data_dir / "live_paper_session.json"
        else:
            self.session_file = Path(session_file)

    def start(self, config: LivePaperSessionConfig) -> None:
        """Initialize paper broker, load strategies, and start live scheduler loop safely in async or sync contexts."""
        if self.state == LivePaperEngineState.RUNNING:
            logger.warning("LivePaperEngine is already running")
            return

        self.config = config
        self.broker = PaperBroker(initial_cash=config.initial_cash)
        self.active_strategies.clear()

        # Load active strategies from registry
        for strat_name in config.strategy_names:
            try:
                strat_inst = StrategyRegistry.instantiate(strat_name)
                self.active_strategies[strat_name.lower()] = strat_inst
                logger.info("Loaded active strategy for live paper trading: {}", strat_name)
            except Exception as err:
                logger.error("Failed to instantiate strategy '{}': {}", strat_name, str(err))

        self.state = LivePaperEngineState.RUNNING
        self.alert_engine.send_alert(
            title="Live Paper Session Started",
            message=f"Started paper session for symbols {config.symbols} with {len(self.active_strategies)} strategies",
            level=AlertLevel.INFO,
        )

        self.save_session()

        # Start loop safely whether in async event loop or sync thread (e.g. Streamlit)
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._run_loop())
        except RuntimeError:
            self._thread = threading.Thread(target=self._run_thread, daemon=True)
            self._thread.start()

    def _run_thread(self) -> None:
        """Background thread entry point running event loop for asyncio coroutines."""
        asyncio.run(self._run_loop())

    def pause(self) -> None:
        """Pause live paper scheduler loop."""
        if self.state == LivePaperEngineState.RUNNING:
            self.state = LivePaperEngineState.PAUSED
            self.alert_engine.send_alert(
                title="Live Paper Session Paused",
                message="Trading scheduler loop paused",
                level=AlertLevel.WARNING,
            )
            self.save_session()

    def resume(self) -> None:
        """Resume paused live paper scheduler loop."""
        if self.state == LivePaperEngineState.PAUSED:
            self.state = LivePaperEngineState.RUNNING
            self.alert_engine.send_alert(
                title="Live Paper Session Resumed",
                message="Trading scheduler loop resumed",
                level=AlertLevel.INFO,
            )
            self.save_session()

    async def stop(self) -> Dict[str, Any]:
        """Stop live session, cancel task, save state, and generate EOD performance report."""
        if self.state == LivePaperEngineState.STOPPED:
            return {}

        self.state = LivePaperEngineState.STOPPED
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("LivePaperEngine session stopped")

        report_summary = {}
        if self.broker and self.config and self.config.auto_eod_report:
            html_path = self.session_file.parent / "eod_report.html"
            json_path = self.session_file.parent / "eod_report.json"
            HTMLReportGenerator.generate(
                self.broker.portfolio, title="Live Paper Trading EOD Report", filepath=html_path
            )
            report_summary = JSONReportGenerator.generate(self.broker.portfolio, filepath=json_path)

        self.alert_engine.send_alert(
            title="Live Paper Session Stopped",
            message=f"Session ended. Total Equity: ${self.broker.portfolio.total_equity:,.2f}"
            if self.broker
            else "Session ended",
            level=AlertLevel.INFO,
        )
        self.save_session()
        return report_summary

    def stop_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for stop() called from Streamlit or sync contexts."""
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.stop())
        except RuntimeError:
            return asyncio.run(self.stop())

    async def _run_loop(self) -> None:
        """Continuous polling loop executing tick evaluations."""
        while self.state in (LivePaperEngineState.RUNNING, LivePaperEngineState.PAUSED):
            if self.state == LivePaperEngineState.RUNNING and self.config:
                try:
                    await self.process_tick()
                except Exception as err:
                    logger.error("Error during live tick processing: {}", str(err))

            interval = self.config.poll_interval_seconds if self.config else 5
            await asyncio.sleep(interval)

    async def process_tick(self) -> List[OrderRequest]:
        """Fetch latest candles for configured symbols, evaluate strategies, and place paper orders."""
        if not self.config or not self.broker:
            return []

        placed_requests: List[OrderRequest] = []

        for symbol in self.config.symbols:
            try:
                # 1. Fetch market candles
                candles_df = self.data_provider.get_candles(symbol, period="5d")
                if candles_df.empty:
                    continue

                self._market_history[symbol.upper()] = candles_df
                latest_row = candles_df.iloc[-1]
                close_price = Decimal(str(latest_row["close"]))

                # Update paper broker market price
                self.broker.set_last_price(symbol, close_price)

                # Build candle object
                candle_obj = Candle(
                    timestamp=candles_df.index[-1]
                    if isinstance(candles_df.index[-1], datetime)
                    else datetime.now(),
                    open=float(latest_row["open"]),
                    high=float(latest_row["high"]),
                    low=float(latest_row["low"]),
                    close=float(latest_row["close"]),
                    volume=int(latest_row["volume"]),
                )

                # 2. Evaluate active strategies
                for strat_name, strategy in self.active_strategies.items():
                    signal = strategy.on_candle(candle_obj, candles_df)
                    if signal and signal.side.value in ("BUY", "SELL"):
                        side = Side.BUY if signal.side.value == "BUY" else Side.SELL
                        req = OrderRequest(
                            symbol=symbol,
                            quantity=10,
                            side=side,
                            order_type=OrderType.MARKET,
                            price=close_price,
                        )

                        # Submit order to paper broker
                        executed_order = await self.broker.place_order(req)
                        placed_requests.append(req)

                        # Dispatch Alert
                        self.alert_engine.send_alert(
                            title=f"LIVE SIGNAL & ORDER: {side.value} {symbol}",
                            message=f"Strategy '{strat_name}' triggered {side.value} for {symbol} @ ${close_price:,.2f}. Order Status: {executed_order.status.value}",
                            level=AlertLevel.INFO,
                        )
            except Exception as err:
                logger.warning("Tick evaluation error for {}: {}", symbol, str(err))

        return placed_requests

    async def inject_demo_order(
        self, symbol: str = "NIFTY", side_str: str = "BUY", quantity: int = 10, price: Optional[float] = None
    ) -> Order:
        """Inject a demo paper order for instant testing of the full execution pipeline."""
        if not self.broker:
            self.broker = PaperBroker(initial_cash=100000.0)

        side = Side.BUY if side_str.upper() == "BUY" else Side.SELL
        order_price = Decimal(str(price)) if price is not None else Decimal("100.0")

        # Update last price in broker
        self.broker.set_last_price(symbol, order_price)

        req = OrderRequest(
            symbol=symbol.upper(),
            quantity=quantity,
            side=side,
            order_type=OrderType.MARKET,
            price=order_price,
        )

        executed_order = await self.broker.place_order(req)
        self.alert_engine.send_alert(
            title=f"DEMO ORDER INJECTED: {side.value} {symbol.upper()}",
            message=f"Injected demo {side.value} order for {quantity} {symbol.upper()} @ ${order_price:,.2f}. Status: {executed_order.status.value}",
            level=AlertLevel.INFO,
        )
        self.save_session()
        return executed_order

    def inject_demo_order_sync(
        self, symbol: str = "NIFTY", side_str: str = "BUY", quantity: int = 10, price: Optional[float] = None
    ) -> Order:
        """Synchronous wrapper for inject_demo_order called from Streamlit or sync contexts."""
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.inject_demo_order(symbol, side_str, quantity, price))
        except RuntimeError:
            return asyncio.run(self.inject_demo_order(symbol, side_str, quantity, price))

    def save_session(self) -> None:
        """Persist current session state and portfolio snapshot to JSON file."""
        if not self.config:
            return

        session_data = {
            "state": self.state.value,
            "config": asdict(self.config),
            "cash": float(self.broker.cash) if self.broker else self.config.initial_cash,
            "saved_at": datetime.now().isoformat(),
        }

        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            logger.debug("Persisted live paper session to {}", self.session_file.name)
        except Exception as err:
            logger.error("Failed to save session state: {}", str(err))

    def recover_session(self) -> bool:
        """Recover session state from JSON file if available."""
        if not self.session_file.exists():
            return False

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            cfg_dict = data.get("config", {})
            if cfg_dict:
                self.config = LivePaperSessionConfig(**cfg_dict)
                self.broker = PaperBroker(initial_cash=data.get("cash", 100000.0))

                for strat_name in self.config.strategy_names:
                    try:
                        self.active_strategies[strat_name.lower()] = StrategyRegistry.instantiate(strat_name)
                    except Exception:
                        pass

                self.state = LivePaperEngineState(data.get("state", "STOPPED"))
                logger.info("Recovered live paper session state: {}", self.state.value)
                return True
        except Exception as err:
            logger.error("Failed to recover session state: {}", str(err))

        return False
