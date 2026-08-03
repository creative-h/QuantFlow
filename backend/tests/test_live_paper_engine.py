"""Unit tests for LivePaperEngine lifecycle, tick processing, session recovery, and reports."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.marketdata.base import MarketDataProvider
from app.paper.live_engine import (
    LivePaperEngine,
    LivePaperEngineState,
    LivePaperSessionConfig,
)


@pytest.fixture
def mock_market_provider() -> MarketDataProvider:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    df = pd.DataFrame(
        {
            "open": [100.0] * 30,
            "high": [105.0] * 30,
            "low": [98.0] * 30,
            "close": [102.0] * 30,
            "volume": [1000] * 30,
        },
        index=dates,
    )
    provider = MagicMock(spec=MarketDataProvider)
    provider.get_candles.return_value = df
    return provider


@pytest.mark.asyncio
async def test_live_paper_engine_lifecycle(tmp_path, mock_market_provider):
    session_file = tmp_path / "live_session.json"
    engine = LivePaperEngine(data_provider=mock_market_provider, session_file=session_file)

    config = LivePaperSessionConfig(
        symbols=["AAPL"],
        strategy_names=["ema"],
        poll_interval_seconds=1,
        initial_cash=50000.0,
        auto_eod_report=True,
    )

    engine.start(config)
    assert engine.state == LivePaperEngineState.RUNNING
    assert engine.broker is not None
    assert "ema" in engine.active_strategies

    # Process single tick manually
    placed = await engine.process_tick()
    assert isinstance(placed, list)

    # Test pause and resume
    engine.pause()
    assert engine.state == LivePaperEngineState.PAUSED

    engine.resume()
    assert engine.state == LivePaperEngineState.RUNNING

    # Stop engine
    summary = await engine.stop()
    assert engine.state == LivePaperEngineState.STOPPED
    assert isinstance(summary, dict)


@pytest.mark.asyncio
async def test_live_paper_session_save_and_recover(tmp_path, mock_market_provider):
    session_file = tmp_path / "live_session.json"
    engine = LivePaperEngine(data_provider=mock_market_provider, session_file=session_file)

    config = LivePaperSessionConfig(
        symbols=["MSFT"],
        strategy_names=["rsi"],
        poll_interval_seconds=2,
        initial_cash=100000.0,
    )
    engine.start(config)
    engine.save_session()
    await engine.stop()

    new_engine = LivePaperEngine(data_provider=mock_market_provider, session_file=session_file)
    recovered = new_engine.recover_session()
    assert recovered is True
    assert new_engine.config.symbols == ["MSFT"]
