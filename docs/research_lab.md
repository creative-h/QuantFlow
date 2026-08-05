# QuantFlow v11.0 Autonomous Learning Engine & Institutional Research Lab

## 1. Overview

QuantFlow v11.0 introduces an **Autonomous Learning Engine & Institutional Research Lab**. Every completed paper trade becomes structured training telemetry. The engine continuously evaluates feature importance, strategy leaderboards, agent scorecards, market regime performance, automated parameter evolution, and self-learning feedback loops.

---

## 2. Core Architecture & Data Pipeline

```
+-----------------------------------------------------------------------+
|                QuantFlow Autonomous Learning Engine                   |
+-----------------------------------------------------------------------+
        |                  |                  |                  |
        v                  v                  v                  v
+---------------+  +---------------+  +---------------+  +---------------+
| Trade Dataset |  |   Feature     |  | Strategy Score|  | Agent Scorecard|
|   Builder     |  | Importance    |  |    Engine     |  |    Engine     |
| - Parquet/CSV |  | - Random Forest| | - Sharpe, Win%|  | - Accuracy %  |
+---------------+  +---------------+  +---------------+  +---------------+
        |                  |                  |                  |
        +------------------+------------------+------------------+
                                   |
                                   v
                        +--------------------+
                        | Self Learning Loop |
                        | - Dynamic Weights  |
                        | - Adaptive Confidence
                        +--------------------+
```

---

## 3. Storage Formats

- **Parquet**: `data/research/trades_dataset.parquet`
- **SQLite**: `data/research/trades_research.db`
- **CSV**: `data/research/trades_dataset.csv`
