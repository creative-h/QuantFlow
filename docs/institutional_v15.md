# QuantFlow v15.0 Institutional Paper Trading Workstation & OMS (Sensibull + Zerodha Kite Style)

## 1. Overview & Architectural Layout

```
+-----------------------------------------------------------------------+
|            Sensibull / Zerodha Kite Style Portfolio Header            |
| Total P&L: -₹26,810 | Unbooked: -₹33,332 | Booked: +₹6,522 | Decay: 0  |
+-----------------------------------------------------------------------+
        |                  |                  |                  |
        v                  v                  v                  v
+---------------+  +---------------+  +---------------+  +---------------+
| Net Positions |  | Strategy      |  | Broker Order  |  | Live Option   |
|   Workstation |  | Groupings     |  |     Book      |  |   Monitor     |
| - Sensibull   |  | - 28th Jul    |  | - Pending     |  | - Intrinsic   |
|   Net Table   |  |   Expiry      |  | - Executed    |  | - Extrinsic   |
+---------------+  +---------------+  +---------------+  +---------------+
        |                  |                  |                  |
        +------------------+------------------+------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                      Autonomous Execution & Auto-Exits                |
| - Auto Exit Engine (Break-Even Stop, ATR Trail, Profit Lock, Time Stop)|
| - Chronological Trade Book Ledger & Position Timeline Replay          |
+-----------------------------------------------------------------------+
```

---

## 2. Sensibull & Zerodha Kite Orderbook Schema

- **Total P&L**: Net sum of realized booked profit and unrealized open positions.
- **Unbooked P&L**: Unrealized mark-to-market profit/loss on active positions.
- **Booked P&L**: Realized profit/loss on closed trades.
- **Strategy Groupings**: Groups position legs by expiration date (e.g. *28th Jul Expiry*, *14th Jul Expiry*).
- **Auto Exit Rules**: Break-even SL move upon Target 1, 50% partial profit booking, ATR 2.0x trailing stop, 45-min time stop.
