"""Unit tests for Strategy Engine, Strategy interface, and PaperBroker routing."""

from datetime import date
from unittest.mock import AsyncMock

import pandas as pd
import pytest

from app.brokers.paper_broker import PaperBroker
from app.marketdata.base import MarketDataProvider
from app.models.dataclasses import Candle, Signal, SignalSide
from app.models.trading import OrderStatus, Side
from app.strategies.ema_crossover import EMACrossoverStrategy
from app.strategies.engine import StrategyEngine


@pytest.fixture
def mock_market_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    # Downtrend then uptrend to trigger fast EMA crossing above slow EMA
    prices = [100.0 - i * 0.5 for i in range(15)] + [92.5 + i * 2.0 for i in range(15)]
    return pd.DataFrame(
        {
            "open": [p - 0.5 for p in prices],
            "high": [p + 1.0 for p in prices],
            "low": [p - 1.0 for p in prices],
            "close": prices,
            "volume": [1000.0] * 30,
        },
        index=dates,
    )


@pytest.mark.asyncio
async def test_strategy_engine_run_with_paper_broker(mock_market_data: pd.DataFrame):
    strategy = EMACrossoverStrategy(fast_period=5, slow_period=10)
    broker = PaperBroker(initial_cash=100000.0)
    engine = StrategyEngine(strategy=strategy, broker=broker, trade_quantity=10)

    mock_provider = AsyncMock(spec=MarketDataProvider)
    mock_provider.get_candles.return_value = mock_market_data

    executed_orders = await engine.run(
        symbol="RELIANCE",
        start=date(2024, 1, 1),
        end=date(2024, 1, 30),
        data_provider=mock_provider,
    )

    assert len(executed_orders) >= 1
    assert executed_orders[0].request.symbol == "RELIANCE"
    assert executed_orders[0].status == OrderStatus.FILLED

    positions = await broker.positions()
    assert len(positions) >= 1
    assert positions[0].symbol == "RELIANCE"


def test_strategy_on_candle_direct():
    strategy = EMACrossoverStrategy(fast_period=3, slow_period=5)
    strategy.initialize()

    dates = pd.date_range("2024-01-01", periods=15, freq="D")
    prices = [100.0 - i * 0.5 for i in range(7)] + [96.5 + i * 3.0 for i in range(8)]

    signals = []
    for dt, price in zip(dates, prices):
        candle = Candle(
            timestamp=dt.to_pydatetime(),
            open=price,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=100,
        )
        sig = strategy.on_candle(candle)
        if sig:
            signals.append(sig)

    assert len(signals) == 15
    buy_signals = [s for s in signals if s.side == SignalSide.BUY]
    assert len(buy_signals) >= 1
