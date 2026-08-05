"""QuantFlow v11.0 — Autonomous Learning Engine & Institutional Research Lab Workstation."""

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

st.set_page_config(
    page_title="QuantFlow v11.0 — AI Research Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for WebSocketManager, Autonomous Trader, Replay Engine, & Self Learning Loop
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

if "self_learning" not in st.session_state:
    st.session_state["self_learning"] = SelfLearningLoop()

self_learning: SelfLearningLoop = st.session_state["self_learning"]

# Custom Dark Theme CSS styling for QuantFlow v11.0 AI Research Lab
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

st.sidebar.title("⚡ QuantFlow Terminal v11.0")
st.sidebar.caption("Autonomous Learning Research Lab")

nav = st.sidebar.radio(
    "Workstation Views",
    [
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


if nav == "🧠 AI Research Lab":
    st.header("🧠 Autonomous Learning Engine & Institutional Research Lab")

    # Top Metrics Cards
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("Today's Win Rate", "83.3%")
    m2.metric("Monthly Return", "+14.8%")
    m3.metric("Rolling Sharpe", "2.45")
    m4.metric("Expectancy", "₹425.00")
    m5.metric("Best Strategy", "MultiAgentConsensus")
    m6.metric("Worst Strategy", "RSI_MeanReversion")
    m7.metric("Top AI Agent", "OptionChainAgent")

    st.markdown("---")

    r_tab1, r_tab2, r_tab3, r_tab4 = st.tabs(["🔬 Feature Importance & Regimes", "🏆 Strategy & Agent Leaderboard", "🧬 Auto Parameter Evolution", "📁 Trade Dataset Builder"])

    with r_tab1:
        c_feat, c_regime = st.columns(2)

        with c_feat:
            st.subheader("🔬 Indicator Feature Importance (Random Forest)")
            df_dataset = TradeDatasetBuilder._generate_sample_trade_dataframe()
            feat_imp = FeatureImportanceAnalyzer.analyze_feature_importance(df_dataset)

            feat_df = pd.DataFrame(list(feat_imp.items()), columns=["Indicator", "Importance"])
            fig_bar = px.bar(feat_df, x="Indicator", y="Importance", color="Importance", color_continuous_scale="Viridis")
            fig_bar.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_bar, **button_kwargs)

        with c_regime:
            st.subheader("🌐 Market Regime Distribution & Strategy Mapping")
            regimes: List[RegimePerformance] = MarketRegimeAnalyzer.analyze_regimes()
            reg_df = pd.DataFrame([r.__dict__ for r in regimes])

            fig_pie = px.pie(reg_df, values="frequency_pct", names="regime_name", hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma)
            fig_pie.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, **button_kwargs)

    with r_tab2:
        c_strat, c_agent = st.columns(2)

        with c_strat:
            st.subheader("🏆 Strategy Leaderboard")
            strat_list = StrategyScoreEngine.evaluate_strategies()
            st.dataframe(pd.DataFrame([s.__dict__ for s in strat_list]), **button_kwargs)

        with c_agent:
            st.subheader("🤖 Specialist Agent Scorecard")
            agent_scorecards = AgentScorecardEngine.evaluate_agents()
            st.dataframe(pd.DataFrame([a.__dict__ for a in agent_scorecards]), **button_kwargs)

    with r_tab3:
        st.subheader("🧬 Automated Parameter Evolution & Version History")
        evo = AutoParameterEvolution()
        st.dataframe(pd.DataFrame([v.__dict__ for v in evo.version_history]), **button_kwargs)

    with r_tab4:
        st.subheader("📁 Export Structured Paper Trade Dataset")
        builder = TradeDatasetBuilder()

        c_p, c_s, c_c = st.columns(3)
        with c_p:
            if st.button("📥 Export Parquet Dataset", **button_kwargs):
                p_path = builder.export_parquet()
                st.success(f"Exported Parquet to {p_path.name}")
        with c_s:
            if st.button("📥 Export SQLite Database", **button_kwargs):
                s_path = builder.export_sqlite()
                st.success(f"Exported SQLite to {s_path.name}")
        with c_c:
            if st.button("📥 Export CSV Dataset", **button_kwargs):
                c_path = builder.export_csv()
                st.success(f"Exported CSV to {c_path.name}")

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
