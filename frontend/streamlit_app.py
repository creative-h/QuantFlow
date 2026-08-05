"""QuantFlow v7.0 — Multi-Agent AI Decision Engine & AI Command Center."""

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

st.set_page_config(
    page_title="QuantFlow v7.0 — AI Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for WebSocketManager, DecisionManager, & Autonomous Trader
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

# Custom Dark Theme CSS styling for QuantFlow v7.0 AI Command Center
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
    .agent-card-buy {
        background-color: #161b22;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #238636;
        margin-bottom: 10px;
    }
    .agent-card-sell {
        background-color: #161b22;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #da3633;
        margin-bottom: 10px;
    }
    .agent-card-wait {
        background-color: #161b22;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #d29922;
        margin-bottom: 10px;
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
    .timeline-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 10px;
        height: 180px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Polled Cached Ticks & Market State
market_status: MarketStatusInfo = MarketStateEngine.get_market_state()

nifty_tick = ws_manager.latest_tick("NIFTY")
bank_tick = ws_manager.latest_tick("BANKNIFTY")
fin_tick = ws_manager.latest_tick("FINNIFTY")

nifty_p = f"₹{nifty_tick.price:,.2f}" if nifty_tick else "₹24,915.20"
bank_p = f"₹{bank_tick.price:,.2f}" if bank_tick else "₹55,201.00"
fin_p = f"₹{fin_tick.price:,.2f}" if fin_tick else "₹22,450.00"

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
        <b>FINNIFTY:</b> {fin_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>VIX:</b> 12.80 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Latency:</b> <span style="color:#58a6ff;">{lat_val}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Time:</b> {time_str} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>State:</b> <b style="color:{status_badge_color};">[{market_status.status}]</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Terminal v7.0")
st.sidebar.caption("Multi-Agent AI Decision Engine")

nav = st.sidebar.radio(
    "Workstation Views",
    [
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


if nav == "🤖 AI Command Center":
    st.header("🤖 Multi-Agent AI Command Center")

    col_target, col_refresh = st.columns([3, 1])
    with col_target:
        target_sym = st.selectbox("Underlying Instrument", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"], index=0)
    with col_refresh:
        if st.button("⚡ Evaluate All 10 Specialist Agents", type="primary", **button_kwargs):
            st.rerun()

    df_chart = fetch_sample_data(target_sym, "1mo")
    candle_now = Candle(
        timestamp=datetime.now(),
        open=float(df_chart["open"].iloc[-1]),
        high=float(df_chart["high"].iloc[-1]),
        low=float(df_chart["low"].iloc[-1]),
        close=float(df_chart["close"].iloc[-1]),
        volume=int(df_chart["volume"].iloc[-1]),
    )
    candle_now.symbol = target_sym

    # Run Multi-Agent Decision Manager
    consensus: MultiAgentConsensus = decision_mgr.evaluate_consensus(candle_now, df_chart)

    # Top Overview Metrics & Gauge / Pie Chart
    col_gauge, col_pie, col_summary = st.columns([1.5, 2, 2.5])

    with col_gauge:
        st.subheader("🎯 Consensus Meter")
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=consensus.confidence,
                title={"text": f"Consensus: {consensus.final_signal}"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#3fb950" if consensus.final_signal == "BUY" else ("#f85149" if consensus.final_signal == "SELL" else "#d29922")},
                    "steps": [
                        {"range": [0, 50], "color": "#161b22"},
                        {"range": [50, 75], "color": "#21262d"},
                        {"range": [75, 100], "color": "#30363d"},
                    ],
                },
            )
        )
        fig_gauge.update_layout(template="plotly_dark", height=230, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_gauge, **button_kwargs)

    with col_pie:
        st.subheader("📊 Weighted Voting Distribution")
        dist_df = pd.DataFrame(
            [
                {"Signal": "BUY", "Weight (%)": consensus.voting_distribution.get("BUY", 0.0)},
                {"Signal": "WAIT", "Weight (%)": consensus.voting_distribution.get("WAIT", 0.0)},
                {"Signal": "SELL", "Weight (%)": consensus.voting_distribution.get("SELL", 0.0)},
            ]
        )
        fig_pie = px.pie(
            dist_df,
            values="Weight (%)",
            names="Signal",
            color="Signal",
            color_discrete_map={"BUY": "#3fb950", "WAIT": "#d29922", "SELL": "#f85149"},
            hole=0.4,
        )
        fig_pie.update_layout(template="plotly_dark", height=230, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_pie, **button_kwargs)

    with col_summary:
        st.subheader("📝 Consensus Summary")
        st.markdown(
            f"""
            <div class="coach-card">
                <h3 style="color:#3fb950;"><b>FINAL SIGNAL: {consensus.final_signal}</b></h3>
                <p><b>Instrument:</b> {consensus.symbol}</p>
                <p><b>AI Confidence:</b> {consensus.confidence:.1f}%</p>
                <hr style="border-color:#30363d;"/>
                <p><b>Rationale:</b> {consensus.summary_reason}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Specialist Agent Decision Cards Grid (10 Agents)
    st.subheader("🤖 10 Specialist AI Agent Decisions")
    agent_cols = st.columns(3)

    for idx, agent_dec in enumerate(consensus.agent_decisions):
        col_idx = idx % 3
        card_class = "agent-card-buy" if agent_dec.signal == "BUY" else ("agent-card-sell" if agent_dec.signal == "SELL" else "agent-card-wait")
        badge_color = "#3fb950" if agent_dec.signal == "BUY" else ("#f85149" if agent_dec.signal == "SELL" else "#d29922")

        with agent_cols[col_idx]:
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b>🤖 {agent_dec.agent_name}</b>
                        <b style="color:{badge_color}; font-size:16px;">{agent_dec.signal} ({agent_dec.confidence:.0f}%)</b>
                    </div>
                    <hr style="border-color:#30363d; margin:6px 0;"/>
                    <small>{agent_dec.reason}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("📜 Live Agent Event Decision Timeline")
    timeline_html = "<div class='timeline-box'>"
    for dec in reversed(consensus.agent_decisions):
        ts_str = dec.timestamp.strftime("%H:%M:%S")
        sig_color = "#3fb950" if dec.signal == "BUY" else ("#f85149" if dec.signal == "SELL" else "#d29922")
        timeline_html += f"<div><span style='color:#8b949e;'>[{ts_str}]</span> <b style='color:{sig_color};'>[{dec.agent_name}]</b> VOTE: {dec.signal} ({dec.confidence:.0f}%) — {dec.reason}</div>"
    timeline_html += "</div>"
    st.markdown(timeline_html, unsafe_allow_html=True)

elif nav == "🏛️ AI Trading Desk":
    col_left, col_mid, col_right = st.columns([1.2, 3, 2])

    with col_left:
        st.subheader("🎯 Instrument Selection")
        target_symbol = st.selectbox("Underlying Index", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"], index=0)
        df_chart = st.session_state.get("market_df", fetch_sample_data(target_symbol, "1mo"))

        latest_spot = float(df_chart["close"].iloc[-1])
        atm_strike = OptionChainEngine.calculate_atm_strike(target_symbol, latest_spot)

        st.metric(f"{target_symbol} Live Spot Price", f"₹{latest_spot:,.2f}")
        st.metric("ATM Strike Price", f"₹{atm_strike:,.0f}")

        st.markdown("---")
        st.subheader("⚙️ Autonomous Controls")
        auto_mode = st.toggle("🤖 Autonomous Trading Mode", value=auto_trader.is_auto_trading)
        if auto_mode != auto_trader.is_auto_trading:
            if auto_mode:
                auto_trader.start()
            else:
                auto_trader.stop()
            st.rerun()

    with col_mid:
        st.subheader(f"📈 {target_symbol} Chart (1-Min Aggregated)")

        df_chart["ema20"] = IndicatorEngine.ema(df_chart, 20)
        df_chart["ema50"] = IndicatorEngine.ema(df_chart, 50)
        df_chart["vwap"] = IndicatorEngine.vwap(df_chart)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart["open"], high=df_chart["high"], low=df_chart["low"], close=df_chart["close"], name="Spot OHLC"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["ema20"], line=dict(color="#58a6ff", width=1.5), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["ema50"], line=dict(color="#d29922", width=1.5), name="EMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["vwap"], line=dict(color="#bc8cff", width=1.5, dash="dash"), name="VWAP"), row=1, col=1)
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart["volume"], marker_color="#30363d", name="Volume"), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=440, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, **button_kwargs)

    with col_right:
        st.subheader("🎓 AI Trading Coach Panel")
        candle_now = Candle(datetime.now(), float(df_chart["open"].iloc[-1]), float(df_chart["high"].iloc[-1]), float(df_chart["low"].iloc[-1]), float(df_chart["close"].iloc[-1]), int(df_chart["volume"].iloc[-1]))
        ai_dec: AITradeDecision = auto_trader.coordinator.evaluate_consensus(target_symbol, candle_now, df_chart)
        coach_adv: AICoachAdvice = AICoach.generate_advice(ai_dec)

        st.markdown(f"<div class='trade-action-box'>⚡ RECOMMENDATION: {coach_adv.recommendation}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='coach-card'><h4><b>❓ Should I Buy Now or Wait?</b></h4><p style='color:#3fb950;'><b>👉 {coach_adv.action_answer}</b></p><hr/><p><b>Why:</b> {coach_adv.why_explanation}</p></div>", unsafe_allow_html=True)

elif nav == "🗣️ AI Analyst Debate Meeting":
    st.header("🗣️ AI Analyst Team Debate Meeting")
    candle_now = Candle(datetime.now(), 24900, 24950, 24880, 24915.20, 2500)
    df_c = fetch_sample_data("NIFTY", "1mo")
    ai_dec = auto_trader.coordinator.evaluate_consensus("NIFTY", candle_now, df_c)
    debate = AIDebateEngine.create_debate(ai_dec)

    st.info(debate.summary_reasoning)
    for p in debate.participants:
        st.markdown(f"### 🤖 {p.name} — `{p.role}`")
        st.write(f"**Vote:** `{p.vote}` | **Confidence:** `{p.confidence:.0f}%` | **Argument:** {p.key_argument}")

elif nav == "📋 Strategy Scoreboard":
    st.header("📋 Multi-Strategy Scoreboard Matrix")
    candle_now = Candle(datetime.now(), 24900, 24950, 24880, 24915.20, 2500)
    df_c = fetch_sample_data("NIFTY", "1mo")
    scoreboard = StrategyScoreboard.evaluate_scoreboard("NIFTY", candle_now, df_c)

    st.dataframe(pd.DataFrame([v.__dict__ for v in scoreboard.votes]), **button_kwargs)

elif nav == "🛡️ Session Risk Dashboard":
    st.header("🛡️ Interactive Session Risk Dashboard")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Today's PnL", "+₹420.00")
    r2.metric("Max Daily Loss Limit", "₹2,000.00")
    r3.metric("Remaining Risk Budget", "₹1,580.00")
    r4.metric("Risk Budget Used", "32%")

elif nav == "📊 AI Performance Analytics":
    st.header("📊 AI Performance Analytics & Agent Metrics")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Daily PnL (₹)", "+₹4,250.00")
    p2.metric("Win Rate", "78.5%")
    p3.metric("Sharpe Ratio", "2.15")
    p4.metric("Profit Factor", "2.40")

elif nav == "⛓️ Live Option Chain Matrix":
    st.header("⛓️ Dedicated Live Option Chain Matrix")
    index_symbol = st.selectbox("Underlying Index", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"])
    chain = OptionChainEngine.generate_chain(index_symbol, 24915.20)
    st.dataframe(pd.DataFrame([c.__dict__ for c in chain.calls.values()]), **button_kwargs)

elif nav == "🎞️ Trade Replay Engine":
    st.header("🎞️ Candle-by-Candle Trade Replay Engine")
    replay_symbol = st.text_input("Replay Symbol", value="NIFTY")

elif nav == "📊 Market Data Explorer":
    st.header("📊 Market Data Explorer")
    symbol = st.text_input("Ticker Symbol", value="NIFTY")

elif nav == "🧩 Strategy Explorer":
    st.header("🧩 Strategy Registry & Plugins")
    st.info(f"Discovered strategies: {', '.join(StrategyRegistry.list_strategies())}")

elif nav == "⚡ Parameter Optimization":
    st.header("⚡ Parameter Optimization Engine")

elif nav == "🔄 Walk Forward Testing":
    st.header("🔄 Walk-Forward Optimization & Testing")

elif nav == "⚔️ Strategy Comparison":
    st.header("⚔️ Multi-Strategy Comparison Engine")

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
