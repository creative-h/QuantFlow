# QuantFlow v16.0 Real Market Paper Trading Engine & Live MTM Workstation

## 1. System Overview & Architecture

```
+-----------------------------------------------------------------------+
|           QuantFlow Real Market Paper Engine (Live Exchange LTP)       |
+-----------------------------------------------------------------------+
        |                  |                  |                  |
        v                  v                  v                  v
+---------------+  +---------------+  +---------------+  +---------------+
|LiveOptionPrice|  |  MTM Engine   |  |  Real Margin  |  | Zerodha Note  |
| - Live WS LTP |  | - Tick MTM PnL|  | - SPAN + Exp  |  | - Taxes & STT |
|   Subscription|  | - Running PnL |  |   Calculator  |  |   Calculator  |
+---------------+  +---------------+  +---------------+  +---------------+
        |                  |                  |                  |
        +------------------+------------------+------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    Validation & Data Quality Layer                    |
| - Live Validation Panel (QuantFlow vs Sensibull vs Zerodha Kite ±0.5%)|
| - Data Quality Heartbeat Engine (Outlier Filtering & WS Auto-Reconnect)|
+-----------------------------------------------------------------------+
```

---

## 2. Zerodha Contract Note Tax Formula Breakdown

| Statutory Tax / Fee | Calculation Rule |
| :--- | :--- |
| **Flat Brokerage** | **₹20.00** per order (₹40 total per round trip trade) |
| **STT (Securities Transaction Tax)** | **0.125%** on Option Sell turnover |
| **Exchange Turnover Charge** | **0.05%** on total buy + sell turnover |
| **GST** | **18%** on (Brokerage + Exchange Charges) |
| **SEBI Turnover Charge** | **₹10 per Crore** |
| **Stamp Duty** | **0.003%** on Option Buy turnover |
