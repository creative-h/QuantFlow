"""Decision Coordinator combining multi-agent sub-scores into a unified AITradeDecision."""

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from app.analytics.multi_agent.agents import (
    MarketRegimeAgent,
    MomentumAgent,
    NewsSentimentAgent,
    OptionsOIAnalyzer,
    RiskAgent,
    TrendAgent,
    VWAPAgent,
)
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.marketdata.option_chain import OptionChain, OptionChainEngine
from app.models.dataclasses import Candle, Signal


class DecisionCoordinator:
    """Coordinator aggregating sub-agent scores into a consensus AITradeDecision object."""

    def __init__(self, min_confidence_threshold: float = 75.0) -> None:
        self.min_confidence_threshold = min_confidence_threshold
        self.trend_agent = TrendAgent()
        self.momentum_agent = MomentumAgent()
        self.vwap_agent = VWAPAgent()
        self.options_oi_agent = OptionsOIAnalyzer()
        self.risk_agent = RiskAgent()
        self.regime_agent = MarketRegimeAgent()
        self.news_agent = NewsSentimentAgent()

    def evaluate_consensus(
        self,
        symbol: str,
        candle: Candle,
        history: pd.DataFrame,
        option_chain: Optional[OptionChain] = None,
        strategy_signal: Optional[Signal] = None,
    ) -> AITradeDecision:
        """Query all sub-agents and synthesize a unified AITradeDecision."""
        sym_clean = symbol.upper()
        spot_price = candle.close

        # Compute VWAP
        vwap_val = history["close"].mean() if history is not None and not history.empty else spot_price * 0.998

        # Option Chain if not provided
        if option_chain is None:
            option_chain = OptionChainEngine.generate_chain(sym_clean, spot_price)

        # Collect Sub-Agent Opinions
        op_trend = self.trend_agent.evaluate(sym_clean, candle, history)
        op_mom = self.momentum_agent.evaluate(sym_clean, candle, history)
        op_vwap = self.vwap_agent.evaluate(sym_clean, candle, vwap_val)
        op_oi = self.options_oi_agent.evaluate(option_chain)
        op_risk = self.risk_agent.evaluate(sym_clean, candle)
        op_regime = self.regime_agent.evaluate(history)
        op_news = self.news_agent.evaluate(sym_clean)

        opinions: List[AgentOpinion] = [
            op_trend,
            op_mom,
            op_vwap,
            op_oi,
            op_risk,
            op_regime,
            op_news,
        ]

        # Calculate weighted consensus score
        weights = {
            "TrendAgent": 0.25,
            "MomentumAgent": 0.20,
            "VWAPAgent": 0.20,
            "OptionsOIAnalyzer": 0.20,
            "RiskAgent": 0.10,
            "MarketRegimeAgent": 0.05,
        }

        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0

        reasons: List[str] = []
        warnings: List[str] = []

        for op in opinions:
            w = weights.get(op.agent_name, 0.0)
            if w > 0:
                total_weight += w
                if op.recommendation == "BULLISH":
                    bullish_score += op.score * w
                    reasons.append(f"✓ {op.agent_name}: {op.reason}")
                elif op.recommendation == "BEARISH":
                    bearish_score += op.score * w
                    reasons.append(f"✓ {op.agent_name}: {op.reason}")
                else:
                    warnings.append(f"⚠️ {op.agent_name}: {op.reason}")

        norm_bullish = bullish_score / total_weight if total_weight > 0 else 50.0
        norm_bearish = bearish_score / total_weight if total_weight > 0 else 50.0

        atm_strike = OptionChainEngine.calculate_atm_strike(sym_clean, spot_price)

        if norm_bullish >= self.min_confidence_threshold and norm_bullish > norm_bearish:
            action = "BUY"
            opt_type = "CE"
            entry = 118.0
            sl = 105.0
            t1, t2, t3 = 135.0, 155.0, 180.0
            confidence = round(norm_bullish, 1)
            rr = "1:2.7"
        elif norm_bearish >= self.min_confidence_threshold:
            action = "BUY"
            opt_type = "PE"
            entry = 115.0
            sl = 102.0
            t1, t2, t3 = 132.0, 150.0, 175.0
            confidence = round(norm_bearish, 1)
            rr = "1:2.5"
        else:
            action = "WAIT"
            opt_type = "CE"
            entry, sl = 118.0, 105.0
            t1, t2, t3 = 135.0, 155.0, 180.0
            confidence = round(max(norm_bullish, norm_bearish), 1)
            rr = "1:2.7"
            warnings.append("⚠️ Consensus confidence below minimum threshold; market watching active")

        return AITradeDecision(
            symbol=sym_clean,
            expiry="Thursday Weekly",
            strike=atm_strike,
            option_type=opt_type,
            action=action,
            entry=entry,
            stop_loss=sl,
            target1=t1,
            target2=t2,
            target3=t3,
            confidence=confidence,
            expected_hold_time="15-30 mins",
            risk_reward=rr,
            reasons=reasons,
            warnings=warnings,
            market_regime=op_regime.reason,
            timestamp=datetime.now(),
            agent_opinions=opinions,
        )
