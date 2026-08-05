"""QuantFlow v10.0 — AI Trading Coach & Performance Auditor Workstation."""

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
from app.analytics.coach_engine import AITradingCoachEngine, LessonsLearned, SetupMatchResult, TradeExplanation
from app.analytics.market_health import MarketHealthMonitor, MarketHealthOverview
from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.debate import AIDebateEngine, AIDebateSession
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.analytics.multi_agent.performance_auditor import AuditReport, PerformanceAuditor
from app.analytics.scoreboard import ScoreboardConsensus, StrategyScoreboard
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
    page_title="QuantFlow v10.0 — AI Trading Coach",
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

# Custom Dark Theme CSS styling for QuantFlow v10.0 AI Trading Coach Workstation
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
    .grade-badge-aplus {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(46, 160, 67, 0.3);
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

st.sidebar.title("⚡ QuantFlow Terminal v10.0")
st.sidebar.caption("AI Trading Coach & Performance Auditor")

nav = st.sidebar.radio(
    "Workstation Views",
    [
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


if nav == "🎓 AI Trading Coach Studio":
    st.header("🎓 AI Trading Coach Studio & Performance Auditor")

    tab_coach, tab_match, tab_audit = st.tabs(["💡 Trade Explanation & Grading", "📊 1,000 Setup Comparator", "📑 Periodic Performance Audit"])

    with tab_coach:
        st.subheader("💡 Deep-Dive Trade Explanation & Trade Grading")

        explanation: TradeExplanation = AITradingCoachEngine.explain_trade(
            symbol="NIFTY", action="BUY", entry=118.0, stop_loss=105.0, target=145.0
        )
        lessons: LessonsLearned = AITradingCoachEngine.grade_trade(risk_compliant=True, followed_plan=True, win_rate=78.5)

        col_exp, col_grade = st.columns([3, 2])

        with col_exp:
            st.markdown(
                f"""
                <div class="coach-card">
                    <h3>⚡ WHY ENTRY: {explanation.symbol} {explanation.action}</h3>
                    <p><b>👉 Entry Rationale:</b> {explanation.why_entry}</p>
                    <p><b>🛑 Stop Loss Rationale:</b> {explanation.why_stop}</p>
                    <p><b>🎯 Target Rationale:</b> {explanation.why_target}</p>
                    <hr style="border-color:#30363d;"/>
                    <p><b>Aligned Indicators:</b> {', '.join(explanation.aligned_indicators)}</p>
                    <p><b>Expected Move:</b> ±₹{explanation.expected_move:.2f} | <b>Win Probability:</b> {explanation.win_probability}%</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_grade:
            st.markdown(f"<div class='grade-badge-aplus'>TRADE GRADE: {lessons.trade_grade}</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="coach-card">
                    <h4><b>📝 Lessons Learned & Suggestions</b></h4>
                    <p><b>Psychology Note:</b> {lessons.psychology_note}</p>
                    <hr style="border-color:#30363d;"/>
                    <p><b>Suggested Improvements:</b></p>
                    <ul>
                        {''.join([f'<li>{imp}</li>' for imp in lessons.suggested_improvements])}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_match:
        st.subheader("📊 1,000 Historical Setup Pattern Comparator")
        match_res: SetupMatchResult = AITradingCoachEngine.compare_setup("NIFTY")

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Historical Setups Compared", f"{match_res.matched_count:,}")
        sm2.metric("Historical Win Rate", f"{match_res.historical_win_rate:.1f}%")
        sm3.metric("Avg Reward-to-Risk", f"{match_res.avg_reward_risk:.2f}:1")
        sm4.metric("Quant Statistical Edge", match_res.confidence_edge)

        st.info(f"Quant Edge: Analyzing 1,000 past occurrences of this setup generated **+₹{match_res.historical_pnl_sum:,.2f}** total historical profit.")

    with tab_audit:
        st.subheader("📑 Periodic Performance Audit Reports")
        rep_type = st.radio("Audit Report Period", ["Daily Report", "Weekly Report", "Monthly Report"], horizontal=True)

        if rep_type == "Daily Report":
            audit: AuditReport = PerformanceAuditor.generate_daily_report()
        elif rep_type == "Weekly Report":
            audit: AuditReport = PerformanceAuditor.generate_weekly_report()
        else:
            audit: AuditReport = PerformanceAuditor.generate_monthly_report()

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Psychology Score", f"{audit.psychology_score:.0f}/100")
        s2.metric("Discipline Score", f"{audit.discipline_score:.0f}/100")
        s3.metric("Risk Score", f"{audit.risk_score:.0f}/100")
        s4.metric("Period Net PnL", f"+₹{audit.net_pnl:,.2f}")

        col_str, col_weak = st.columns(2)
        with col_str:
            st.success(f"**Strengths:**\n- " + "\n- ".join(audit.strengths))
            st.info(f"**Most Profitable Setup:** {audit.most_profitable_setup}")
        with col_weak:
            st.warning(f"**Weaknesses:**\n- " + "\n- ".join(audit.weaknesses))
            st.error(f"**Worst Setup:** {audit.worst_setup}")

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
