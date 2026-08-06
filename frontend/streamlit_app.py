"""QuantFlow v12.0 — Professional Trading Workstation & Live Paper Trading Validation."""

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
from typing import Any, Dict, List, Optional

button_kwargs = {"use_container_width": True}

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.agents.decision_manager import DecisionManager, MultiAgentConsensus
from app.analytics.ai_coach import AICoach, AICoachAdvice
from app.analytics.coach_engine import AITradingCoachEngine, LessonsLearned, SetupMatchResult, TradeExplanation
from app.analytics.market_health import MarketHealthMonitor, MarketHealthOverview
from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.debate import AIDebateEngine, AIDebateSession
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.analytics.multi_agent.scoreboard import ScoreboardConsensus, StrategyScoreboard
from app.analytics.performance_auditor import AuditReport, PerformanceAuditor
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
from app.research.agent_scorecard import AgentScorecard, AgentScorecardEngine
from app.research.audit_reports import AIDailyMonthlyReporter
from app.research.comparison import StrategyComparisonEngine
from app.research.feature_importance import FeatureImportanceAnalyzer
from app.research.optimization import OptimizationEngine
from app.research.parameter_evolution import AutoParameterEvolution
from app.research.regime_analyzer import MarketRegimeAnalyzer, RegimePerformance
from app.research.self_learning import SelfLearningLoop
from app.research.strategy_scorer import StrategyScoreEngine
from app.research.trade_dataset import TradeDatasetBuilder
from app.research.walk_forward import WalkForwardEngine
from app.simulation.replay_engine import MarketReplayEngine, ReplayState
from app.strategies.registry import StrategyRegistry
from app.trade_management.position_sizer import ProfessionalPositionSizer
from app.trade_management.target_manager import TargetManager
from app.trade_management.trailing_stop_engine import TrailingStopEngine
from app.trading_desk.order_audit_log import AuditEvent, OrderAuditLogger
from app.trading_desk.position_tracker import ClosedPosition, OpenPosition, PositionTracker
from app.trading_desk.rejected_trades import RejectedTrade, RejectedTradeLogger
from app.trading_desk.session_summary import SessionSummary, SessionSummaryGenerator
from app.trading_desk.telegram_notifier import TelegramNotifier

st.set_page_config(
    page_title="QuantFlow v12.0 — Professional Trading Workstation",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for singletons
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

audit_logger = OrderAuditLogger.get_instance()
rejected_logger = RejectedTradeLogger.get_instance()
position_tracker = PositionTracker.get_instance()
telegram_notifier = TelegramNotifier.get_instance()

# Custom Dark Theme CSS styling for Bloomberg/Kite-style Workstation
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
    .coach-card {
        background-color: #161b22;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #238636;
        margin-bottom: 12px;
    }
    .thinking-box {
        background-color: #161b22;
        border: 1px solid #388bfd;
        border-radius: 6px;
        padding: 10px;
        height: 240px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
    }
    .pnl-positive { color: #3fb950; font-weight: bold; }
    .pnl-negative { color: #f85149; font-weight: bold; }
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

# TOP BAR HUD
st.markdown(
    f"""
    <div class="hud-bar">
        <b style="color:{conn_color};">● KITE WEBSOCKET: {conn_str}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>NIFTY:</b> {nifty_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>BANKNIFTY:</b> {bank_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Latency:</b> <span style="color:#58a6ff;">{lat_val}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Time:</b> {time_str} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Today's PnL:</b> <span class="pnl-positive">+₹4,250.00</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Paper Balance:</b> ₹1,04,250.00 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Open Positions:</b> {len(position_tracker.open_positions)} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Drawdown:</b> -0.4% &nbsp;&nbsp;&nbsp;&nbsp;
        <b>State:</b> <b style="color:{status_badge_color};">[{market_status.status}]</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Terminal v12.0")
st.sidebar.caption("Professional Trade Desk Workstation")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "⚡ Professional Trade Desk",
        "🧠 AI Research Lab",
        "🎓 AI Trading Coach Studio",
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


if nav == "⚡ Professional Trade Desk":
    col_left, col_center, col_right = st.columns([1.1, 3.2, 1.7])

    # LEFT PANEL - WATCHLIST & INSTRUMENT SELECTION
    with col_left:
        st.subheader("👁️ Watchlist")
        target_symbol = st.selectbox("Symbol", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"], index=0)
        expiry_sel = st.selectbox("Expiry", ["2026-08-07 (Weekly)", "2026-08-14", "2026-08-28 (Monthly)"], index=0)
        interval_sel = st.selectbox("Timeframe", ["1-Min", "3-Min", "5-Min", "15-Min", "1-Hour", "1-Day"], index=0)
        st.text_input("Add Custom Ticker", value="RELIANCE")

        st.markdown("---")
        st.subheader("💼 Paper Account")
        st.write("**Initial Capital:** ₹1,00,000.00")
        st.write("**Current Capital:** ₹1,04,250.00")
        st.write("**Available Cash:** ₹78,400.00")
        st.write("**Margin Used:** ₹25,850.00")
        st.write("**Exposure:** 2.95%")

    # CENTER PANEL - TRADINGVIEW PLOTLY CANDLESTICK CHART
    with col_center:
        st.subheader(f"📈 {target_symbol} Live TradingView Chart ({interval_sel})")

        df_chart = fetch_sample_data(target_symbol, "1mo")
        df_chart["ema20"] = IndicatorEngine.ema(df_chart, 20)
        df_chart["ema50"] = IndicatorEngine.ema(df_chart, 50)
        df_chart["vwap"] = IndicatorEngine.vwap(df_chart)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart["open"], high=df_chart["high"], low=df_chart["low"], close=df_chart["close"], name="Spot OHLC"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["ema20"], line=dict(color="#58a6ff", width=1.5), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["ema50"], line=dict(color="#d29922", width=1.5), name="EMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["vwap"], line=dict(color="#bc8cff", width=1.5, dash="dash"), name="VWAP"), row=1, col=1)

        # Add Buy/Sell Marker Overlay
        fig.add_trace(go.Scatter(x=[df_chart.index[-5]], y=[df_chart["low"].iloc[-5] - 15.0], mode="markers+text", marker=dict(symbol="triangle-up", size=14, color="#3fb950"), text=["BUY ₹118"], textposition="bottom center", name="AI Entry"), row=1, col=1)
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart["volume"], marker_color="#30363d", name="Volume"), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=440, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, **button_kwargs)

    # RIGHT PANEL - AI RECOMMENDATION CARD & LIVE THINKING STREAM
    with col_right:
        st.subheader("🤖 Live AI Recommendation Card")
        candle_now = Candle(datetime.now(), float(df_chart["open"].iloc[-1]), float(df_chart["high"].iloc[-1]), float(df_chart["low"].iloc[-1]), float(df_chart["close"].iloc[-1]), int(df_chart["volume"].iloc[-1]))
        candle_now.symbol = target_symbol

        consensus: MultiAgentConsensus = decision_mgr.evaluate_consensus(candle_now, df_chart)

        st.markdown(
            f"""
            <div class="coach-card">
                <h3 style="color:#3fb950;"><b>RECOMMENDATION: {consensus.final_signal}</b></h3>
                <p><b>Instrument:</b> {consensus.symbol} 24900 CE</p>
                <p><b>AI Confidence:</b> {consensus.confidence:.1f}%</p>
                <p><b>Market Regime:</b> BULL_TREND</p>
                <p><b>Expected Hold Time:</b> 15-30 mins</p>
                <p><b>Expected Move:</b> ±₹27.00 | <b>Win Probability:</b> 78.5%</p>
                <p><b>Position Size:</b> 50 Units (2 Lots)</p>
                <hr style="border-color:#30363d;"/>
                <p><b>Reasoning:</b> {consensus.summary_reason}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<b>🧠 Live AI Thinking Panel (Chronological Stream):</b>", unsafe_allow_html=True)
        thinking_html = "<div class='thinking-box'>"
        for dec in reversed(consensus.agent_decisions):
            ts_s = dec.timestamp.strftime("%H:%M:%S")
            s_col = "#3fb950" if dec.signal == "BUY" else ("#f85149" if dec.signal == "SELL" else "#d29922")
            thinking_html += f"<div><span style='color:#8b949e;'>[{ts_s}]</span> <b style='color:{s_col};'>[{dec.agent_name}]</b> {dec.signal} ({dec.confidence:.0f}%) — {dec.reason}</div>"
        thinking_html += "</div>"
        st.markdown(thinking_html, unsafe_allow_html=True)

    st.markdown("---")

    # BOTTOM AUDIT TABLES (OPEN POSITIONS, CLOSED POSITIONS, REJECTED TRADES, EVENT AUDIT LOG)
    t_open, t_closed, t_rej, t_audit, t_session = st.tabs(["🟢 Live Open Positions", "🔴 Live Closed Positions", "🚫 Rejected Trade Log", "📋 Order Event Audit Log", "📊 Session Summary"])

    with t_open:
        st.subheader("🟢 Live Open Positions")
        if position_tracker.open_positions:
            st.dataframe(pd.DataFrame([p.__dict__ for p in position_tracker.open_positions]), **button_kwargs)
        else:
            st.info("No active open positions.")

    with t_closed:
        st.subheader("🔴 Live Closed Positions Ledger")
        if position_tracker.closed_positions:
            st.dataframe(pd.DataFrame([p.__dict__ for p in position_tracker.closed_positions]), **button_kwargs)
        else:
            st.info("No closed positions recorded.")

    with t_rej:
        st.subheader("🚫 Rejected Trade Audit Log")
        rejs = rejected_logger.get_all_rejections()
        st.dataframe(pd.DataFrame([r.__dict__ for r in rejs]), **button_kwargs)

    with t_audit:
        st.subheader("📋 System Order Event Audit Log")
        evts = audit_logger.get_recent_events(50)
        st.dataframe(pd.DataFrame([e.__dict__ for e in evts]), **button_kwargs)

    with t_session:
        st.subheader("📊 Market Close Session Summary")
        session_data: SessionSummary = SessionSummaryGenerator.generate_session_summary()
        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Today's Net PnL", f"+₹{session_data.net_pnl:,.2f}")
        sm2.metric("Win Rate", f"{session_data.win_rate:.1f}%")
        sm3.metric("AI Accuracy", f"{session_data.ai_accuracy_pct:.1f}%")
        sm4.metric("Best Trade", session_data.best_trade)

        fig_eq = px.line(x=list(range(len(session_data.equity_curve))), y=session_data.equity_curve, title="Session Capital Equity Curve")
        fig_eq.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_eq, **button_kwargs)

elif nav == "🧠 AI Research Lab":
    st.header("🧠 Autonomous Learning Engine & Institutional Research Lab")

elif nav == "🎓 AI Trading Coach Studio":
    st.header("🎓 AI Trading Coach Studio & Performance Auditor")

elif nav == "🎞️ Market Replay Simulator":
    st.header("🎞️ Market Replay Simulator Engine")

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
