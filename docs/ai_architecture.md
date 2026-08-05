# QuantFlow v7.0 Multi-Agent AI Architecture & Decision Engine

## 1. Overview

QuantFlow v7.0 implements an institutional **Multi-Agent AI System**. Rather than relying on a single trading strategy, QuantFlow deploys 10 independent specialist AI agents. Each agent evaluates a specific market vector (trend, momentum, institutional VWAP, volume spikes, price action patterns, option chain matrix, open interest buildup, PCR sentiment, India VIX volatility, and pre-trade risk limits).

A central `DecisionManager` combines their opinions using a weighted voting system to produce a unified trade signal.

---

## 2. Agent System Architecture

```
                                +---------------------------+
                                |      Market Tick & OHLC   |
                                +---------------------------+
                                              |
     +----------------------------------------+----------------------------------------+
     |                |                       |                       |                |
     v                v                       v                       v                v
+----------+   +--------------+       +---------------+       +---------------+   +----------+
| Trend    |   | Momentum     |       | VWAP Agent    |       | Volume Agent  |   | Price    |
| Agent    |   | Agent        |       | (app/agents/  |       | (app/agents/  |   | Action   |
| (30%)    |   | (15%)        |       | vwap_agent.py)|       | volume_agent) |   | (10%)    |
+----------+   +--------------+       +---------------+       +---------------+   +----------+
     |                |                       |                       |                |
     +----------------+-----------------------+-----------------------+----------------+
                                              |
     +----------------------------------------+----------------------------------------+
     |                |                       |                       |                |
     v                v                       v                       v                v
+----------+   +--------------+       +---------------+       +---------------+   +----------+
| Option   |   | OI Agent     |       | PCR Agent     |       | Volatility    |   | Risk     |
| Chain    |   | (app/agents/ |       | (app/agents/  |       | Agent         |   | Agent    |
| (20%)    |   | oi_agent.py) |       | pcr_agent.py) |       | (3%)          |   | (2%)     |
+----------+   +--------------+       +---------------+       +---------------+   +----------+
     |                |                       |                       |                |
     +----------------+-----------------------+-----------------------+----------------+
                                              |
                                              v
                            +-----------------------------------+
                            |         DecisionManager           |
                            |  - Weighted Voting Engine         |
                            |  - Consensus Calibration          |
                            +-----------------------------------+
                                              |
                                              v
                            +-----------------------------------+
                            | Final Signal: BUY / SELL / WAIT   |
                            | Confidence: 0 - 100%              |
                            +-----------------------------------+
```

---

## 3. Specialist Agent Weights

| Agent Name | Market Vector Evaluated | Weighted Voting Weight |
| :--- | :--- | :--- |
| **TrendAgent** | EMA 20/50, SMA 200, Supertrend, ADX | **30%** |
| **OptionChainAgent** | Max Pain, Highest Call/Put OI, Call Writing | **20%** |
| **MomentumAgent** | RSI 14, MACD, Stochastic, CCI | **15%** |
| **VWAPAgent** | Institutional VWAP levels & distance | **10%** |
| **PriceActionAgent** | Pin Bar, Engulfing, Inside Bar, Breakouts | **10%** |
| **VolumeAgent** | Volume Spike ratio vs SMA20 | **5%** |
| **PCRAgent** | Overall PCR, OI PCR, Volume PCR | **5%** |
| **VolatilityAgent** | India VIX regime, ATR(14), Expected Move | **3%** |
| **RiskAgent** | Daily Loss Limit, Position Size, Exposure | **2%** |

---

## 4. Consensus Decision Logic

Each agent outputs an `AgentDecision` object:
```python
@dataclass
class AgentDecision:
    agent_name: str
    signal: str       # "BUY", "SELL", "WAIT"
    confidence: float # 0.0 to 100.0
    reason: str
    metrics: Dict[str, Any]
```

The `DecisionManager` calculates weighted signal percentages:
$$\text{BUY\_Weight} = \sum_{i \in \text{BUY}} w_i, \quad \text{SELL\_Weight} = \sum_{j \in \text{SELL}} w_j, \quad \text{WAIT\_Weight} = \sum_{k \in \text{WAIT}} w_k$$

If $\text{BUY\_Weight} \ge \text{WAIT\_Weight}$ and Weighted Confidence $\ge 70.0\%$, the final signal is **`BUY`**.
