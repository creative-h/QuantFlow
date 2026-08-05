"""QuantFlow v8.0 — Professional Trade Management Workstation."""

import sys
from pathlib import Path

# Unconditionally force backend directory to position 0 in sys.path
backend_dir = str((Path(__file__).parent.parent / "backend").resolve())
if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

import asyncio
from datetime import datetime
import json
import time

button_kwargs = {"use_container_width": True}

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.agents.decision_manager import DecisionManager, MultiAgentConsensus
from app.analytics.ai_coach import AICoach, AICoachAdvice
from app.analytics.market_health import MarketHealthMonitor, MarketHealthOverview
from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.debate import AIDebateEngine, AIDebateSession
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.analytics.multi_agent.scoreboard import ScoreboardConsensus, StrategyScoreboard
from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.indicators.engine import IndicatorEngine
from app.marketdata.live_feed import Tick
from app.marketdata.market_state import MarketStateEngine, MarketStatusInfo
from app.marketdata.option_chain import OptionChain, OptionChainEngine
from app.marketdata.tick_cache import TickCache
from app.marketdata.websocket_manager import WebSocketManager
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.models.dataclasses import Candle
from app.paper.autonomous_trader import AutonomousPaperTrader
from app.paper.state_machine import TradeState
from app.research.comparison import StrategyComparisonEngine
from app.research.optimization import OptimizationEngine
from app.research.walk_forward import WalkForwardEngine
from app.strategies.registry import StrategyRegistry
from app.trade_management.position_sizer import ProfessionalPositionSizer
from app.trade_management.target_manager import TargetManager
from app.trade_management.trailing_stop_engine import TrailingStopEngine

st.set_page_config(
    page_title="QuantFlow v8.0 — Trade Management Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for WebSocketManager & Autonomous Trader
if "ws_manager" not in st.session_state:
    st.session_state["ws_manager"] = WebSocketManager()
    st.session_state["ws_manager"].connect()

ws_manager: WebSocketManager = st.session_state["ws_manager"]

if "decision_mgr" not in st.session_state:
    st.session_state["decision_mgr"] = DecisionManager()

decision_mgr: DecisionManager = st.session_state["decision_mgr"]

if "auto_trader" not in st.session_state:
    st.session_state["auto_trader"] = AutonomousPaperTrader()

auto_trader: AutonomousPaperTrader = st.session_state["auto_trader"]

# Custom Dark Theme CSS styling for QuantFlow v8.0 Trade Management Workstation
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    .hud-bar {
        background-color: #161b22;
        padding: 10px 16px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 13px;
        margin-bottom: 12px;
        border: 1px solid #30363d;
    }
    .trade-card {
        background-color: #161b22;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #388bfd;
        margin-bottom: 12px;
    }
    .coach-card {
        background-color: #161b22;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #238636;
        margin-bottom: 12px;
    }
    .trade-action-box {
        background: linear-gradient(90deg, #1f6beb 0%, #2ea043 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Polled Cached Ticks & Market State
market_status: MarketStatusInfo = MarketStateEngine.get_market_state()

nifty_tick = ws_manager.latest_tick("NIFTY")
bank_tick = ws_manager.latest_tick("BANKNIFTY")

nifty_p = f"₹{nifty_tick.price:,.2f}" if nifty_tick else "₹24,915.20"
bank_p = f"₹{bank_tick.price:,.2f}" if bank_tick else "₹55,201.00"

conn_str = "CONNECTED" if ws_manager.is_connected() else "SIMULATED / RECONNECTING"
conn_color = "#3fb950" if ws_manager.is_connected() else "#d29922"
lat_val = f"{ws_manager.tick_cache.get_latency_ms('NIFTY'):.1f}ms"
time_str = market_status.timestamp.strftime("%H:%M:%S IST")
status_badge_color = "#3fb950" if market_status.status == "OPEN" else "#f85149"

# TOP TICKER HUD
st.markdown(
    f"""
    <div class="hud-bar">
        <b style="color:{conn_color};">● KITE WEBSOCKET: {conn_str}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>NIFTY:</b> {nifty_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>BANKNIFTY:</b> {bank_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>VIX:</b> 12.80 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Latency:</b> <span style="color:#58a6ff;">{lat_val}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Time:</b> {time_str} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>State:</b> <b style="color:{status_badge_color};">[{market_status.status}]</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Terminal v8.0")
st.sidebar.caption("Professional Trade Management Engine")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "🎯 Trade Management Studio",
        "🤖 AI Command Center",
        "🏛️ AI Trading Desk",
        "🗣️ AI Analyst Debate Meeting",
        "📋 Strategy Scoreboard",
        "🛡️ Session Risk Dashboard",
        "📊 AI Performance Analytics",
        "⛓️ Live Option Chain Matrix",
        "🎞️ Trade Replay Engine",
        "📊 Market Data Explorer",
        "🧩 Strategy Explorer",
        "⚡ Parameter Optimization",
        "🔄 Walk Forward Testing",
        "⚔️ Strategy Comparison",
        "📄 Reports & Analytics",
    ],
)


# Helper function to fetch market data safely
def fetch_sample_data(symbol: str = "NIFTY", period: str = "1mo") -> pd.DataFrame:
    try:
        provider = YahooFinanceProvider()
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(provider.get_candles(symbol, period=period))
        except Exception:
            return asyncio.run(provider.get_candles(symbol, period=period))
    except Exception:
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        import numpy as np

        np.random.seed(42)
        base = 24900.0 if "NIFTY" in symbol.upper() else 55000.0
        price = base + np.cumsum(np.random.randn(100) * 15.0)
        return pd.DataFrame(
            {
                "open": price - 10.0,
                "high": price + 25.0,
                "low": price - 20.0,
                "close": price,
                "volume": 250000,
            },
            index=dates,
        )


if nav == "🎯 Trade Management Studio":
    st.header("🎯 Professional Trade Management Studio")

    t1, t2 = st.tabs(["⚡ Live Trade Cards & Scaling", "📝 Pro Trade Journal & Reports"])

    with t1:
        st.subheader("📌 Active Live Trade Position Cards")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Remaining Risk Budget", "₹1,580.00")
        c2.metric("Current Risk-Reward", "1:2.7")
        c3.metric("Holding Duration", "18 mins")
        c4.metric("Exit Reason", "TARGET_1_HIT")
        c5.metric("Expected Profit", "+₹4,250.00")
        c6.metric("Win Probability", "78.5%")

        st.markdown("---")
        col_trade_card, col_sizer = st.columns([3, 2])

        with col_trade_card:
            st.markdown(
                """
                <div class="trade-card">
                    <h3>⚡ ACTIVE TRADE: NIFTY 24900 CE</h3>
                    <p><b>Entry Price:</b> ₹118.00 | <b>Current Price:</b> ₹132.50 | <b>Stop Loss:</b> ₹118.00 <span style="color:#3fb950;">(Moved to Cost!)</span></p>
                    <p><b>Target 1 (50%):</b> ₹135.00 <span style="color:#3fb950;">[HIT - 50% EXITED]</span></p>
                    <p><b>Target 2 (30%):</b> ₹155.00 [PENDING]</p>
                    <p><b>Target 3 (20%):</b> ₹180.00 [PENDING]</p>
                    <hr style="border-color:#30363d;"/>
                    <p><b>Unrealized PnL:</b> <span style="color:#3fb950; font-size:18px;"><b>+₹1,450.00 (+12.2%)</b></span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_sizer:
            st.subheader("🧮 Kelly Criterion & Risk Position Sizer")
            port_val = st.number_input("Portfolio Capital (₹)", value=100000.0)
            win_rate = st.slider("Historical Win Rate (%)", 30.0, 90.0, 65.0)
            rr_ratio = st.slider("Reward-to-Risk Ratio", 1.0, 5.0, 2.5)

            kelly_frac = ProfessionalPositionSizer.calculate_kelly_fraction(win_rate, rr_ratio)
            sizer_res = ProfessionalPositionSizer.calculate_risk_based_size(port_val, 2.0, 118.0, 105.0)

            st.info(f"Calculated Kelly Fraction: **{kelly_frac * 100:.2f}%** | Max Capital Allocation: **₹{port_val * kelly_frac:,.2f}**")
            st.success(f"Risk-Based Quantity: **{sizer_res['quantity']} units** ({sizer_res['lots']} Lots) | Risk Amount: **₹{sizer_res['actual_risk']}**")

    with t2:
        st.subheader("📝 Pro Trade Journaling & AI Emotion Logger")

        j_col1, j_col2 = st.columns([2, 3])
        with j_col1:
            trade_symbol = st.text_input("Trade Contract Symbol", value="NIFTY 24900 CE")
            entry_p = st.number_input("Entry Price (₹)", value=118.0)
            exit_p = st.number_input("Exit Price (₹)", value=135.0)
            emotion = st.selectbox("Trader Emotion", ["Disciplined", "FOMO", "Greedy", "Anxious", "Neutral"])
            reason = st.text_area("Trade Entry Rationale", value="EMA20 crossover above EMA50 with strong VWAP bounce.")
            notes = st.text_area("AI Coach Notes", value="Trade executed in strict compliance with 2.0% risk limits. Move SL to Cost triggered upon T1.")

            if st.button("💾 Save Trade Journal Entry", type="primary", **button_kwargs):
                st.success(f"Logged trade for {trade_symbol} with emotion tag [{emotion}]!")

        with j_col2:
            st.subheader("📄 Generate & Download Trade Report")
            rep_data = {
                "Contract": trade_symbol,
                "Entry Price": f"₹{entry_p:.2f}",
                "Exit Price": f"₹{exit_p:.2f}",
                "PnL": f"₹{(exit_p - entry_p) * 50:.2f}",
                "Emotion Tag": emotion,
                "Rationale": reason,
                "AI Notes": notes,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.json(rep_data)

            st.download_button(
                "📥 Download Trade Journal Report (JSON)",
                data=json.dumps(rep_data, indent=2),
                file_name="trade_journal_report.json",
                mime="application/json",
            )

elif nav == "🤖 AI Command Center":
    st.header("🤖 Multi-Agent AI Command Center")

elif nav == "🏛️ AI Trading Desk":
    col_left, col_mid, col_right = st.columns([1.2, 3, 2])
    with col_left:
        target_symbol = st.selectbox("Underlying Index", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"], index=0)
        df_chart = st.session_state.get("market_df", fetch_sample_data(target_symbol, "1mo"))

elif nav == "🗣️ AI Analyst Debate Meeting":
    st.header("🗣️ AI Analyst Team Debate Meeting")

elif nav == "📋 Strategy Scoreboard":
    st.header("📋 Multi-Strategy Scoreboard Matrix")

elif nav == "🛡️ Session Risk Dashboard":
    st.header("🛡️ Interactive Session Risk Dashboard")

elif nav == "📊 AI Performance Analytics":
    st.header("📊 AI Performance Analytics & Agent Metrics")

elif nav == "⛓️ Live Option Chain Matrix":
    st.header("⛓️ Dedicated Live Option Chain Matrix")

elif nav == "🎞️ Trade Replay Engine":
    st.header("🎞️ Candle-by-Candle Trade Replay Engine")

elif nav == "📊 Market Data Explorer":
    st.header("📊 Market Data Explorer")

elif nav == "🧩 Strategy Explorer":
    st.header("🧩 Strategy Registry & Plugins")

elif nav == "⚡ Parameter Optimization":
    st.header("⚡ Parameter Optimization Engine")

elif nav == "🔄 Walk Forward Testing":
    st.header("🔄 Walk-Forward Optimization & Testing")

elif nav == "⚔️ Strategy Comparison":
    st.header("⚔️ Multi-Strategy Comparison Engine")

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
