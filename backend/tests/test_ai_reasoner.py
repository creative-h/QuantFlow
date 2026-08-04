"""Unit tests for AIReasoner engine."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from app.analytics.ai_reasoner import AIExplanation, AIReasoner, MarketRegime
from app.models.dataclasses import Candle, Signal, SignalSide


@pytest.fixture
def sample_candle() -> Candle:
    return Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=105.0,
        low=98.0,
        close=102.5,
        volume=2500,
    )


@pytest.fixture
def sample_history() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(30))
    return pd.DataFrame(
        {"open": close - 0.5, "high": close + 1.0, "low": close - 1.0, "close": close, "volume": 3000},
        index=dates,
    )


def test_ai_reasoner_evaluate_buy_signal(sample_candle, sample_history):
    signal = Signal(side=SignalSide.BUY, price=102.5, confidence=0.85)
    explanation = AIReasoner.evaluate("NIFTY", sample_candle, sample_history, signal=signal)

    assert isinstance(explanation, AIExplanation)
    assert explanation.decision == "BUY"
    assert explanation.confidence_score >= 80.0
    assert "Bullish" in explanation.explanation
    assert explanation.symbol == "NIFTY"


def test_ai_reasoner_evaluate_sell_signal(sample_candle, sample_history):
    signal = Signal(side=SignalSide.SELL, price=102.5, confidence=0.82)
    explanation = AIReasoner.evaluate("NIFTY", sample_candle, sample_history, signal=signal)

    assert explanation.decision == "SELL"
    assert explanation.confidence_score >= 80.0
    assert "Bearish" in explanation.explanation


def test_ai_reasoner_evaluate_hold_signal(sample_candle, sample_history):
    explanation = AIReasoner.evaluate("AAPL", sample_candle, sample_history, signal=None)

    assert explanation.decision == "HOLD"
    assert explanation.confidence_score == 60.0
    assert explanation.market_regime in list(MarketRegime)


def test_market_regime_enum_values():
    assert MarketRegime.TRENDING_BULLISH.value == "TRENDING_BULLISH"
    assert MarketRegime.TRENDING_BEARISH.value == "TRENDING_BEARISH"
    assert MarketRegime.MEAN_REVERTING.value == "MEAN_REVERTING"
    assert MarketRegime.CONSOLIDATING.value == "CONSOLIDATING"


def test_ai_explanation_extra_metrics(sample_candle, sample_history):
    explanation = AIReasoner.evaluate("RELIANCE", sample_candle, sample_history)
    assert "close" in explanation.extra_metrics
    assert explanation.extra_metrics["volume"] == 2500
