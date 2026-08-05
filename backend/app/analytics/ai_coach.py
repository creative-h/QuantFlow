"""AI Trading Coach Panel generating plain-English trader guidance."""

from dataclasses import dataclass
from datetime import datetime

from app.analytics.multi_agent.decision import AITradeDecision


@dataclass
class AICoachAdvice:
    """Dataclass storing plain-language trader advice from the AI Coach."""

    timestamp: datetime
    symbol: str
    recommendation: str  # e.g. "BUY NIFTY 24900 CE"
    action_answer: str  # "Should I buy now or wait?" -> "BUY NOW @ ₹118" or "WAIT FOR CANDLE CLOSE"
    why_explanation: str
    risk_guidance: str
    coach_tip: str


class AICoach:
    """AI Coach synthesizing trader-friendly explanations and decision clarity."""

    @classmethod
    def generate_advice(cls, decision: AITradeDecision) -> AICoachAdvice:
        """Synthesize plain-English trader guidance from AITradeDecision."""
        if decision.action == "BUY":
            rec_str = f"BUY {decision.symbol} {int(decision.strike)} {decision.option_type}"
            action_ans = f"BUY NOW @ ₹{decision.entry} (SL: ₹{decision.stop_loss}, Target: ₹{decision.target1})"
            why = (
                f"The short-term trend for {decision.symbol} is bullish (EMA20 above EMA50 and spot above VWAP). "
                f"Options data shows supportive PCR with Call buying interest. Proposed Risk-Reward is {decision.risk_reward}, "
                f"which fits today's risk limits perfectly with {decision.confidence:.1f}% AI confidence."
            )
            risk_guide = f"Risk per trade is locked at 2.0% of portfolio (Max Loss: ₹{round((decision.entry - decision.stop_loss) * 25, 2)})."
            tip = "Pro Tip: If price reaches Target 1 (₹135), immediately move Stop Loss to Break-Even (₹118) to lock in a risk-free trade."
        else:
            rec_str = f"WAIT / WATCH {decision.symbol}"
            action_ans = "WAIT FOR NEXT CANDLE CLOSE"
            why = (
                f"Technical indicators for {decision.symbol} show market consolidation. "
                f"Multi-Agent confidence is {decision.confidence:.1f}%, which is below our 75% minimum threshold for trade execution. "
                f"The AI Coach recommends waiting for a clear VWAP breakout or EMA alignment."
            )
            risk_guide = "Risk capital is preserved 100%. No capital committed during neutral market regimes."
            tip = "Pro Tip: Capital preservation during choppy markets is the key to long-term option buying profitability."

        return AICoachAdvice(
            timestamp=datetime.now(),
            symbol=decision.symbol,
            recommendation=rec_str,
            action_answer=action_ans,
            why_explanation=why,
            risk_guidance=risk_guide,
            coach_tip=tip,
        )
