# QuantFlow v14.0 Institutional AI Trading Operating System

## 1. Overview & System Architecture

```
+-----------------------------------------------------------------------+
|             QuantFlow Institutional AI Trading Operating System       |
+-----------------------------------------------------------------------+
        |                  |                  |                  |
        v                  v                  v                  v
+---------------+  +---------------+  +---------------+  +---------------+
|  Prediction   |  |  Live Option  |  | Portfolio Risk|  | Performance   |
|   Tracker &   |  |   Analytics   |  |    Engine     |  |     Lab       |
| Calibration   |  |  Greeks/Pain  |  | Agg Greeks    |  | Sharpe/Sortino|
+---------------+  +---------------+  +---------------+  +---------------+
        |                  |                  |                  |
        +------------------+------------------+------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                      Learning & Research Core                         |
| - Strategy Lab Leaderboard (EMA, VWAP, ORB, SuperTrend, ICT, SMC)     |
| - Evening AI Coach Daily Reports & PDF/HTML Exports                   |
| - ML Telemetry Dataset Builder (Parquet, SQLite, CSV)                 |
+-----------------------------------------------------------------------+
```

---

## 2. API Endpoints & Data Schema

- `PredictionTracker.compute_accuracy_metrics()`: Evaluates accuracy %, calibration error, and prediction logs.
- `ConfidenceCalibrator.calculate_calibration()`: Calculates Brier Score and Expected Calibration Error (ECE).
- `OptionAnalyticsEngine.get_strike_analytics()`: Live Option Greeks (Delta, Gamma, Theta, Vega), IV, IV Percentile, Max Pain, Expected Move.
- `PortfolioRiskEngine.get_portfolio_risk()`: Aggregated Portfolio Delta, Gamma, Theta, Vega, Margin, Exposure %, and Risk Heatmap.
- `PerformanceLabEngine.calculate_performance()`: Sharpe, Sortino, Calmar, Profit Factor, Recovery Factor, Expectancy, and Kelly %.
- `StrategyLabEngine.rank_all_strategies()`: Multi-strategy Leaderboard across 8 strategy plugins.
