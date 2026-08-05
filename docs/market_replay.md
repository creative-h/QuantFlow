# QuantFlow v9.0 Market Replay Simulator Engine

## 1. Overview

QuantFlow v9.0 introduces an interactive **Market Replay Simulator Engine**. The engine provides historical candle-by-candle and tick-by-tick simulation for `NIFTY` and `BANKNIFTY`, allowing traders to pause, rewind, step forward, fast-forward, and watch AI Multi-Agent teams analyze historical price action in real time.

---

## 2. Replay Simulator Architecture

```
+-----------------------------------------------------------------------+
|                       MarketReplayEngine                              |
| - Playback State: IDLE, PLAYING, PAUSED, COMPLETED                    |
| - Speed Controller: 1x (1.0s), 5x (0.2s), 10x (0.1s), 100x (0.01s)     |
+-----------------------------------------------------------------------+
        |                  |                  |                  |
        v                  v                  v                  v
+---------------+  +---------------+  +---------------+  +---------------+
| Playback Loop |  | Step Controls |  | Multi-Agent AI|  | Order Ledger  |
| - Thread-safe |  | - Step Forward|  | - Evaluates   |  | - Simulated   |
| - Speed Delays|  | - Step Back   |  |   each bar    |  |   Exits & PnL |
+---------------+  +---------------+  +---------------+  +---------------+
```

---

## 3. Playback Controls & Speed Multipliers

- **Play / Pause**: Non-blocking background thread daemon advancing historical bars.
- **Step Forward (1 Bar / Tick)**: Advance historical index by 1 candle.
- **Step Backward (1 Bar / Tick)**: Rewind historical index by 1 candle.
- **Speed Multipliers**:
  - `1x`: 1 second delay per bar (normal speed).
  - `5x`: 0.2 second delay per bar.
  - `10x`: 0.1 second delay per bar.
  - `100x`: 0.01 second delay per bar (instantaneous replay).
