"""Volume Agent evaluating volume spikes, average volume, and delivery ratio."""

from typing import Dict, Optional
import pandas as pd

from app.agents.decision import AgentDecision
from app.models.dataclasses import Candle


class VolumeAgent:
    """Specialist AI Agent analyzing volume confirmation, spikes, and delivery ratios."""

    def __init__(self, name: str = "VolumeAgent") -> None:
        self.name = name

    def evaluate(self, candle: Candle, df: pd.DataFrame) -> AgentDecision:
        """Evaluate Volume spike ratio vs 20-period volume SMA."""
        if df.empty or len(df) < 5 or "volume" not in df:
            return AgentDecision(
                agent_name=self.name,
                signal="WAIT",
                confidence=50.0,
                reason="Insufficient volume telemetry",
                metrics={"volume_ratio": 1.0},
            )

        vol_sma = df["volume"].tail(20).mean()
        vol_sma = max(1.0, vol_sma)
        cur_vol = candle.volume
        vol_ratio = round(cur_vol / vol_sma, 2)

        if vol_ratio >= 1.5:
            signal = "BUY"
            conf = min(92.0, 70.0 + (vol_ratio * 10.0))
            reason = f"High volume spike: Volume ({cur_vol:,}) is {vol_ratio}x 20-bar average ({int(vol_sma):,})"
        elif vol_ratio >= 1.0:
            signal = "BUY"
            conf = 72.0
            reason = f"Above average volume: Volume ({cur_vol:,}) is {vol_ratio}x average"
        else:
            signal = "WAIT"
            conf = 50.0
            reason = f"Below average volume: Volume ({cur_vol:,}) is {vol_ratio}x average"

        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=round(conf, 1),
            reason=reason,
            metrics={"volume": cur_vol, "volume_sma": int(vol_sma), "volume_ratio": vol_ratio},
        )
