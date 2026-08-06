# QuantFlow Autonomous Institutional Paper Trading System

## 1. System Architecture

```
+-----------------------------------------------------------------------+
|             QuantFlow Autonomous Institutional Paper System           |
+-----------------------------------------------------------------------+
        |                  |                  |                  |
        v                  v                  v                  v
+---------------+  +---------------+  +---------------+  +---------------+
|MarketIntegrity|  |ExecutionPipe  |  |RealisticBroker|  | TradeExplainer|
| - Cross-feed  |  | - 8-Stage     |  | - Brokerage ₹20| | - Numerical   |
|   Validation  |  |   Status Bar  |  | - STT, GST    |  |   Breakdown   |
+---------------+  +---------------+  +---------------+  +---------------+
        |                  |                  |                  |
        +------------------+------------------+------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                     System Telemetry & Audit Layer                    |
| - Live Trade Book & Lifecycle Timeline (SCANNED -> APPROVED -> ACTIVE)|
| - Option Greeks (Delta, Gamma, Theta, Vega) & Live RR                 |
| - Backtest vs Paper Trade Comparison Engine                           |
| - Autonomous System Health Monitor (WS/API Latency, CPU, Memory)      |
+-----------------------------------------------------------------------+
```

---

## 2. Realistic Execution Cost Breakdown (Paper Trading)

| Cost Component | Rate / Formula |
| :--- | :--- |
| **Flat Brokerage** | **₹20.00** per executed order |
| **STT (Securities Transaction Tax)** | **0.125%** on Option Sell side premium turnover |
| **Exchange Turnover Charges** | **0.05%** |
| **GST** | **18%** on (Brokerage + Exchange Charges) |
| **SEBI Turnover Fee** | **₹10 per Crore** |
| **Stamp Duty** | **0.003%** on Option Buy side turnover |
| **Slippage Simulation** | **0.05%** adverse execution fill price drift |
| **Execution Delay** | **50ms** simulated order routing latency |
