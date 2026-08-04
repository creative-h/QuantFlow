"""Unit tests for AIReasoner engine and OptionTradeRecommendation."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from app.analytics.ai_reasoner import (
    AIExplanation,
    AIReasoner,
    MarketRegime,
    OptionTradeRecommendation,
)
from app.models.dataclasses import Candle, Signal, SignalSide


@pytest.fixture
def sample_candle() -> Candle:
    return Candle(
        timestamp=datetime.now(),
        open=24900.0,
        high=24950.0,
        low=24880.0,
        close=24915.20,
        volume=2500,
    )


@pytest.fixture
def sample_history() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    close = 24900.0 + np.cumsum(np.random.randn(30) * 10.0)
    return pd.DataFrame(
        {"open": close - 5.0, "high": close + 15.0, "low": close - 15.0, "close": close, "volume": 30000},
        index=dates,
    )


def test_ai_reasoner_evaluate_buy_signal(sample_candle, sample_history):
    signal = Signal(side=SignalSide.BUY, price=24915.20, confidence=0.85)
    explanation = AIReasoner.evaluate("NIFTY", sample_candle, sample_history, signal=signal)

    assert isinstance(explanation, AIExplanation)
    assert explanation.decision == "BUY"
    assert explanation.confidence_score >= 80.0
    assert explanation.option_recommendation is not None
    assert explanation.option_recommendation.option_type == "CE"
    assert explanation.option_recommendation.action == "BUY"


def test_ai_reasoner_evaluate_sell_signal(sample_candle, sample_history):
    signal = Signal(side=SignalSide.SELL, price=24915.20, confidence=0.82)
    explanation = AIReasoner.evaluate("NIFTY", sample_candle, sample_history, signal=signal)

    assert explanation.decision == "SELL"
    assert explanation.confidence_score >= 80.0
    assert explanation.option_recommendation is not None
    assert explanation.option_recommendation.option_type == "PE"


def test_ai_reasoner_evaluate_hold_signal(sample_candle, sample_history):
    explanation = AIReasoner.evaluate("NIFTY", sample_candle, sample_history, signal=None)

    assert explanation.decision == "HOLD"
    assert explanation.market_regime in list(MarketRegime)


def test_market_regime_enum_values():
    assert MarketRegime.TRENDING_BULLISH.value == "TRENDING_BULLISH"
    assert MarketRegime.TRENDING_BEARISH.value == "TRENDING_BEARISH"
    assert MarketRegime.MEAN_REVERTING.value == "MEAN_REVERTING"
    assert MarketRegime.CONSOLIDATING.value == "CONSOLIDATING"


def test_ai_explanation_option_recommendation_fields(sample_candle, sample_history):
    explanation = AIReasoner.evaluate("BANKNIFTY", sample_candle, sample_history)
    rec = explanation.option_recommendation
    assert rec is not None
    assert isinstance(rec, OptionTradeRecommendation)
    assert "BANKNIFTY" in rec.contract_symbol
    assert rec.entry_price > 0.0
    assert rec.stop_loss < rec.entry_price
    assert rec.target_price > rec.entry_price
