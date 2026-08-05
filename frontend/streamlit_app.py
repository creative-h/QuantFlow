"""QuantFlow v9.0 — Market Replay Simulator Workstation."""

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
from app.simulation.replay_engine import MarketReplayEngine, ReplayState
from app.strategies.registry import StrategyRegistry
from app.trade_management.position_sizer import ProfessionalPositionSizer
from app.trade_management.target_manager import TargetManager
from app.trade_management.trailing_stop_engine import TrailingStopEngine

st.set_page_config(
    page_title="QuantFlow v9.0 — Market Replay Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for WebSocketManager, Autonomous Trader, & Replay Engine
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

if "replay_engine" not in st.session_state:
    st.session_state["replay_engine"] = MarketReplayEngine(symbol="NIFTY")

replay_engine: MarketReplayEngine = st.session_state["replay_engine"]

# Custom Dark Theme CSS styling for QuantFlow v9.0 Market Replay Simulator
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
    .replay-control-bar {
        background-color: #161b22;
        padding: 12px 18px;
        border-radius: 8px;
        border: 1px solid #388bfd;
        margin-bottom: 14px;
    }
    .thoughts-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 12px;
        height: 220px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
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

st.sidebar.title("⚡ QuantFlow Terminal v9.0")
st.sidebar.caption("Market Replay Simulator Engine")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "🎞️ Market Replay Simulator",
        "🎯 Trade Management Studio",
        "🤖 AI Command Center",
        "🏛️ AI Trading Desk",
        "🗣️ AI Analyst Debate Meeting",
        "📋 Strategy Scoreboard",
        "🛡️ Session Risk Dashboard",
        "📊 AI Performance Analytics",
        "⛓️ Live Option Chain Matrix",
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


if nav == "🎞️ Market Replay Simulator":
    st.header("🎞️ Market Replay Simulator Engine")

    rep_state: ReplayState = replay_engine.get_state()

    # Playback Control Strip UI
    st.markdown("<div class='replay-control-bar'>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1.5, 1.5, 2])

    with c1:
        if st.button("▶️ Play", **button_kwargs):
            replay_engine.play()
            st.rerun()
    with c2:
        if st.button("⏸️ Pause", **button_kwargs):
            replay_engine.pause()
            st.rerun()
    with c3:
        if st.button("◀️ Step Back", **button_kwargs):
            replay_engine.step_backward(1)
            st.rerun()
    with c4:
        if st.button("▶️ Step Fwd", **button_kwargs):
            replay_engine.step_forward(1)
            st.rerun()
    with c5:
        speed = st.select_slider("Speed", options=[1.0, 5.0, 10.0, 100.0], value=rep_state.speed_multiplier, format_func=lambda x: f"{int(x)}x")
        if speed != rep_state.speed_multiplier:
            replay_engine.set_speed(speed)
    with c6:
        st.metric("Replay Status", f"[{rep_state.status}]")
    with c7:
        st.metric("Bar Progress", f"{rep_state.current_index}/{rep_state.total_bars}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Replay Candlestick Chart & AI Telemetry
    col_chart, col_ai = st.columns([3, 2])

    with col_chart:
        sub_df = replay_engine.df.iloc[: rep_state.current_index + 1]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=sub_df.index, open=sub_df["open"], high=sub_df["high"], low=sub_df["low"], close=sub_df["close"], name="Replay Price"), row=1, col=1)
        fig.add_trace(go.Bar(x=sub_df.index, y=sub_df["volume"], marker_color="#30363d", name="Volume"), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=420, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, **button_kwargs)

    with col_ai:
        st.subheader("💡 Live AI Thoughts & Replay Telemetry")
        m1, m2 = st.columns(2)
        m1.metric("Simulated Realized PnL", f"+₹{rep_state.realized_pnl:,.2f}")
        m2.metric("Executed Orders", f"{rep_state.orders_count}")

        st.markdown("<b>📜 AI Decision Thoughts Log:</b>", unsafe_allow_html=True)
        thoughts_html = "<div class='thoughts-box'>"
        for thought in reversed(replay_engine.ai_thoughts):
            thoughts_html += f"<div>{thought}</div>"
        thoughts_html += "</div>"
        st.markdown(thoughts_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Replay Executed Orders Ledger")
    if replay_engine.orders:
        st.dataframe(pd.DataFrame([o.__dict__ for o in replay_engine.orders]), **button_kwargs)
    else:
        st.info("No orders executed yet in the current replay playback window.")

elif nav == "🎯 Trade Management Studio":
    st.header("🎯 Professional Trade Management Studio")

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
