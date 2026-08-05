"""Strategy Scoreboard Consensus Engine evaluating strategy plugin alignment."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from app.models.dataclasses import Candle
from app.strategies.registry import StrategyRegistry


@dataclass
class StrategyVote:
    """Dataclass storing vote from an individual strategy plugin."""

    strategy_name: str
    vote: str  # "BUY", "SELL", "WAIT"
    confidence: float  # 0 to 100
    description: str


@dataclass
class ScoreboardConsensus:
    """Dataclass storing strategy consensus tally and alignment metrics."""

    timestamp: datetime
    votes: List[StrategyVote] = field(default_factory=list)
    buy_count: int = 0
    sell_count: int = 0
    wait_count: int = 0
    consensus_recommendation: str = "WAIT"
    alignment_score: float = 50.0  # 0 to 100


class StrategyScoreboard:
    """Scoreboard evaluating strategy plugin consensus across all registered strategies."""

    @classmethod
    def evaluate_scoreboard(cls, symbol: str, candle: Candle, history: pd.DataFrame) -> ScoreboardConsensus:
        """Run all registered strategies against current market data and compute consensus vote tally."""
        StrategyRegistry.discover_strategies()
        registered_names = StrategyRegistry.list_strategies()

        votes: List[StrategyVote] = []
        buy_c, sell_c, wait_c = 0, 0, 0

        for name in registered_names:
            try:
                strat_inst = StrategyRegistry.instantiate(name)
                sig = strat_inst.on_candle(candle, history)
                if sig and sig.side.value == "BUY":
                    vote_str = "BUY"
                    conf = 85.0
                    buy_c += 1
                    desc = f"{name.upper()} strategy generated BUY signal"
                elif sig and sig.side.value == "SELL":
                    vote_str = "SELL"
                    conf = 80.0
                    sell_c += 1
                    desc = f"{name.upper()} strategy generated SELL signal"
                else:
                    vote_str = "WAIT"
                    conf = 50.0
                    wait_c += 1
                    desc = f"{name.upper()} strategy holding neutral position"

                votes.append(StrategyVote(name.upper(), vote_str, conf, desc))
            except Exception:
                votes.append(StrategyVote(name.upper(), "WAIT", 50.0, f"{name.upper()} strategy neutral"))
                wait_c += 1

        total_strats = len(votes) if votes else 1
        if buy_c >= sell_c and buy_c >= wait_c and buy_c > 0:
            consensus_rec = "BUY"
            alignment = (buy_c / total_strats) * 100.0
        elif sell_c > buy_c and sell_c >= wait_c:
            consensus_rec = "SELL"
            alignment = (sell_c / total_strats) * 100.0
        else:
            consensus_rec = "WAIT"
            alignment = (wait_c / total_strats) * 100.0

        return ScoreboardConsensus(
            timestamp=datetime.now(),
            votes=votes,
            buy_count=buy_c,
            sell_count=sell_c,
            wait_count=wait_c,
            consensus_recommendation=consensus_rec,
            alignment_score=round(alignment, 1),
        )
