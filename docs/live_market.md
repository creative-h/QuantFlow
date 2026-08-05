# QuantFlow v3.0 Live Market Engine Architecture & Infrastructure

## 1. Executive Summary

The **QuantFlow v3.0 Live Market Engine** is an institutional-grade, zero-latency market infrastructure powered by Zerodha Kite Connect WebSocket (`KiteTicker`) and REST APIs. It feeds real-time tick telemetry into a thread-safe `TickCache`, aggregates multi-timeframe candles (`1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `1d`), evaluates current market operational phase (`PREOPEN`, `OPEN`, `POST MARKET`, `CLOSED`), and computes live Option Chains complete with Black-Scholes Option Greeks (**Delta, Gamma, Theta, Vega**), Max Pain, PCR, and Support/Resistance levels.

---

## 2. Architecture & Data Flow

```
+-----------------------------------------------------------------------+
|                    Zerodha KiteTicker WebSocket                       |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|            WebSocketManager (backend/app/marketdata/websocket_manager.py)
|   - Single Connection Lifecycle | Auto-Reconnect | Heartbeat Daemon   |
+-----------------------------------------------------------------------+
                |                                         |
                v                                         v
+-------------------------------+       +-------------------------------+
|          TickCache            |       |        CandleBuilder          |
| (app/marketdata/tick_cache.py)|       | (app/marketdata/candle_builder|
| - In-Memory Lock Guarded      |       | - Multi-TF (1m, 3m, 5m, 15m..)|
| - Instant Price & Greek Lookup|       | - Emits Completed Candles     |
+-------------------------------+       +-------------------------------+
                |                                         |
                +--------------------+--------------------+
                                     |
                                     v
+-----------------------------------------------------------------------+
|                    Streamlit Workstation UI                           |
|   - Top Ticker HUD | TradingView Plotly Chart | Live AI Panel      |
|   - Bottom Option Chain Matrix with Greeks & Highlighting             |
+-----------------------------------------------------------------------+
```

---

## 3. Core Modules Overview

### 3.1 WebSocket Manager (`app/marketdata/websocket_manager.py`)
- Thread-safe wrapper managing `KiteTicker` background threads.
- Automatically re-subscribes instrument tokens after network drops.
- Monitors heartbeat state every 5 seconds.

### 3.2 Live Tick Cache (`app/marketdata/tick_cache.py`)
- Memory-resident cache indexed by `instrument_token` and symbol string.
- Stores `last_price`, `bid`, `ask`, `volume`, `oi`, `ohlc`, `change`, and `timestamp`.

### 3.3 Multi-Timeframe Candle Builder (`app/marketdata/candle_builder.py`)
- Converts streaming ticks into candles across `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `1d`.
- Computes volume-weighted average price (VWAP) and Open Interest (OI) per candle.

### 3.4 Market State Engine (`app/marketdata/market_state.py`)
- Detects Indian market timings:
  - **PREOPEN**: 09:00 - 09:15 IST
  - **OPEN**: 09:15 - 15:30 IST
  - **POST MARKET**: 15:30 - 16:00 IST
  - **CLOSED**: After 16:00 IST, weekends, and NSE market holidays.

### 3.5 Option Chain Engine & Greeks (`app/marketdata/option_chain.py`)
- Automatic discovery for `NIFTY`, `BANKNIFTY`, `FINNIFTY`, `MIDCPNIFTY`, `SENSEX`.
- Calculates **ATM Strike**, **ITM/OTM**, **Max Pain**, **PCR**, **Highest Call/Put OI**, **Highest Change OI**, and Black-Scholes Greeks (**Delta, Gamma, Theta, Vega**).

---

## 4. Operational Recovery & Resilience

- **Network Interruption**: Exponential backoff reconnect retry loop (`1s`, `2s`, `4s`, `8s`, max `30s`).
- **Session Expiry**: Re-authenticates via QuantFlow `ZerodhaAuthSession`.
- **UI Decoupling**: Streamlit UI non-blocking polling directly from `TickCache`.
