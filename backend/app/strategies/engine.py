"""Strategy Engine orchestrating historical data, indicators, strategy evaluation, signals, and broker execution."""

from datetime import date
from typing import Optional

import pandas as pd
from loguru import logger

from app.brokers.base import Broker
from app.brokers.paper_broker import PaperBroker
from app.marketdata.base import MarketDataProvider
from app.models.dataclasses import Candle, Signal, SignalSide
from app.models.trading import Order, OrderRequest, OrderType, Side
from app.strategies.base import Strategy


class StrategyEngine:
    """Orchestrates strategy execution against historical or live candle streams and routes signals to a Broker."""

    def __init__(
        self,
        strategy: Strategy,
        broker: Optional[Broker] = None,
        trade_quantity: int = 10,
    ) -> None:
        self.strategy = strategy
        self.broker = broker or PaperBroker()
        self.trade_quantity = trade_quantity
        self.history: list[Candle] = []

    async def run(
        self,
        symbol: str,
        start: date,
        end: date,
        data_provider: MarketDataProvider,
        interval: str = "1d",
    ) -> list[Order]:
        """Run strategy over historical data fetched from MarketDataProvider."""
        logger.info("Initializing strategy engine run for '{}' ({} to {})", symbol, start, end)

        self.strategy.initialize()
        df = await data_provider.get_candles(symbol, start=start, end=end, interval=interval)

        if df.empty:
            logger.warning("No market data returned for strategy run on {}", symbol)
            return []

        orders_executed: list[Order] = []

        for ts, row in df.iterrows():
            candle = Candle.from_series(row)
            candle.timestamp = pd.to_datetime(ts).to_pydatetime()

            if isinstance(self.broker, PaperBroker):
                self.broker.set_last_price(symbol, candle.close)

            self.history.append(candle)
            signal = self.strategy.on_candle(candle)

            if signal and signal.side != SignalSide.HOLD:
                signal.symbol = symbol
                signal.timestamp = candle.timestamp
                order = await self._execute_signal(signal, symbol, candle.close)
                if order:
                    orders_executed.append(order)
                    self.strategy.on_order(order)

        logger.info(
            "Strategy engine completed run on {}: {} total candles processed, {} orders executed",
            symbol,
            len(df),
            len(orders_executed),
        )
        return orders_executed

    async def _execute_signal(
        self, signal: Signal, symbol: str, current_price: float
    ) -> Optional[Order]:
        """Convert Signal to OrderRequest and execute via Broker interface."""
        order_side = Side.BUY if signal.side == SignalSide.BUY else Side.SELL
        price = signal.price if signal.price > 0 else current_price

        order_request = OrderRequest(
            symbol=symbol,
            quantity=self.trade_quantity,
            side=order_side,
            order_type=OrderType.MARKET,
            price=price,
        )

        try:
            logger.info(
                "Strategy generated signal {} -> placing order with Broker", signal.side.value
            )
            order = await self.broker.place_order(order_request)
            return order
        except Exception as err:
            logger.error("Failed to execute order for signal {}: {}", signal.side.value, str(err))
            return None
