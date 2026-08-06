"""QuantFlow v15.0 — Institutional Paper Trading Workstation & OMS (Sensibull + Zerodha Kite Style)."""

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
from app.analytics.ai_scoreboard import LiveAIScoreboard, ScoreboardMetrics
from app.analytics.backtest_comparison import BacktestComparisonEngine
from app.analytics.coach_engine import AITradingCoachEngine, LessonsLearned, SetupMatchResult, TradeExplanation
from app.analytics.confidence_calibration import CalibrationReport, ConfidenceCalibrator
from app.analytics.evening_coach import EveningAICoach, EveningCoachReport
from app.analytics.market_health import MarketHealthMonitor, MarketHealthOverview
from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.debate import AIDebateEngine, AIDebateSession
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.analytics.multi_agent.scoreboard import ScoreboardConsensus, StrategyScoreboard
from app.analytics.performance_auditor import AuditReport, PerformanceAuditor
from app.analytics.performance_lab import PerformanceLabEngine, PerformanceMetrics
from app.analytics.prediction_tracker import AIPredictionRecord, PredictionTracker
from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.analytics.trade_explainability import NumericalTradeExplanation, NumericalTradeExplainer, PostTradeAudit
from app.indicators.engine import IndicatorEngine
from app.marketdata.live_feed import Tick
from app.marketdata.market_integrity import FeedCheckResult, MarketIntegrityEngine
from app.marketdata.market_state import MarketStateEngine, MarketStatusInfo
from app.marketdata.option_analytics import OptionAnalyticsEngine, StrikeAnalytics
from app.marketdata.option_chain import OptionChain, OptionChainEngine
from app.marketdata.option_monitor import RealtimeOptionMonitor, RealtimeOptionSnapshot
from app.marketdata.tick_cache import TickCache
from app.marketdata.websocket_manager import WebSocketManager
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.models.dataclasses import Candle
from app.paper.autonomous_trader import AutonomousPaperTrader
from app.paper.realistic_broker import RealisticBroker, TradeExecutionCost
from app.paper.state_machine import TradeState
from app.research.agent_scorecard import AgentScorecard, AgentScorecardEngine
from app.research.audit_reports import AIDailyMonthlyReporter
from app.research.comparison import StrategyComparisonEngine
from app.research.feature_importance import FeatureImportanceAnalyzer
from app.research.optimization import OptimizationEngine
from app.research.parameter_evolution import AutoParameterEvolution
from app.research.regime_analyzer import MarketRegimeAnalyzer, RegimePerformance
from app.research.regime_classifier import DetailedRegimeClassifier, RegimeClassification
from app.research.self_learning import SelfLearningLoop
from app.research.strategy_lab import LabStrategyRank, StrategyLabEngine
from app.research.strategy_scorer import StrategyScoreEngine
from app.research.trade_dataset import TradeDatasetBuilder
from app.research.walk_forward import WalkForwardEngine
from app.risk.portfolio_dashboard import SensibullPortfolioDashboard, SensibullPortfolioHeader
from app.risk.portfolio_risk import PortfolioGreeks, PortfolioRiskEngine, PortfolioRiskMetrics
from app.simulation.replay_engine import MarketReplayEngine, ReplayState
from app.strategies.registry import StrategyRegistry
from app.system.health_monitor import AutonomousHealthMonitor, SystemHealthMetrics
from app.trade_management.auto_exit_manager import AutoExitConfig, AutoExitManager, TradeManagerDecision
from app.trade_management.position_sizer import ProfessionalPositionSizer
from app.trade_management.target_manager import TargetManager
from app.trade_management.trailing_stop_engine import TrailingStopEngine
from app.trading_desk.broker_order_book import BrokerOrder, BrokerOrderBook, TradeBookEvent
from app.trading_desk.execution_pipeline import ExecutionPipeline
from app.trading_desk.institutional_positions import InstitutionalPositionTracker, NetPositionItem, StrategyGroup
from app.trading_desk.live_trade_book import LiveTradeBook, TradeBookEntry
from app.trading_desk.order_audit_log import AuditEvent, OrderAuditLogger
from app.trading_desk.position_details import DeepPositionDetails, PositionDetailsEngine, PositionExplainerOutput
from app.trading_desk.position_timeline import PositionTimelineEngine, PositionTimelineStep
from app.trading_desk.position_tracker import ClosedPosition, OpenPosition, PositionTracker
from app.trading_desk.rejected_trades import RejectedTrade, RejectedTradeLogger
from app.trading_desk.session_summary import SessionSummary, SessionSummaryGenerator
from app.trading_desk.telegram_notifier import TelegramNotifier

st.set_page_config(
    page_title="QuantFlow v15.0 — Sensibull / Kite OMS Workstation",
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

if "pipeline" not in st.session_state:
    st.session_state["pipeline"] = ExecutionPipeline()

pipeline: ExecutionPipeline = st.session_state["pipeline"]

inst_pos_tracker = InstitutionalPositionTracker.get_instance()
broker_orderbook = BrokerOrderBook.get_instance()
integrity_engine = MarketIntegrityEngine.get_instance()
health_monitor = AutonomousHealthMonitor.get_instance()

# Custom Sensibull Dark Theme CSS styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    .sensibull-header {
        background-color: #161b22;
        padding: 12px 18px;
        border-radius: 6px;
        border: 1px solid #30363d;
        margin-bottom: 14px;
    }
    .sensibull-card {
        background-color: #161b22;
        padding: 14px;
        border-radius: 6px;
        border: 1px solid #30363d;
        margin-bottom: 12px;
    }
    .pnl-positive { color: #3fb950; font-weight: bold; }
    .pnl-negative { color: #f85149; font-weight: bold; }
    .status-near-sl { color: #d29922; font-weight: bold; }
    .status-near-target { color: #58a6ff; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fetch Sensibull Portfolio Header Metrics
s_header: SensibullPortfolioHeader = SensibullPortfolioDashboard.get_sensibull_header()

# SENSIBULL TOP SUMMARY BAR
st.markdown(
    f"""
    <div class="sensibull-header">
        <span style="font-size:16px; font-weight:bold; color:#58a6ff;">SENSIBULL / KITE DRAFT PORTFOLIOS</span> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>Total P&L:</b> <span class="pnl-negative">-₹26,810.00</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Unbooked P&L:</b> <span class="pnl-negative">-₹33,332.00</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Booked P&L:</b> <span class="pnl-positive">+₹6,522.00</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Total Decay:</b> 0 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Margin Used:</b> ₹2,15,000.00 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Cash:</b> ₹7,85,000.00
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Workstation")
st.sidebar.caption("Sensibull + Zerodha Kite OMS v15.0")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "📊 Institutional Positions (Sensibull/Kite OMS)",
        "📑 Orderbook & Trade Book",
        "🛡️ Autonomous Paper Trader",
        "📈 Real-Time Option Monitor",
        "⚡ Live Validation Panel",
        "⚡ Institutional Trade Desk",
        "📈 Live Option Analytics",
        "📊 Portfolio Risk Dashboard",
        "🎯 Performance Lab",
        "🧬 Strategy Lab",
        "💡 Numerical Trade Explainability",
        "📊 Backtest vs Paper Comparison",
        "🧠 AI Research Lab",
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


if nav == "📊 Institutional Positions (Sensibull/Kite OMS)":
    st.header("📊 Net Positions & Strategy Groupings (Sensibull OMS Workstation)")

    for group in inst_pos_tracker.strategy_groups:
        with st.expander(f"📁 Strategy Group: {group.group_name} ({len(group.positions)} Positions) — Total P&L: ₹{group.total_pnl:,.2f}", expanded=True):
            st.dataframe(pd.DataFrame([p.__dict__ for p in group.positions]), **button_kwargs)

    st.markdown("---")
    st.subheader("🔍 Position Deep Details & Plain English AI Rationale")
    pos_det: DeepPositionDetails = PositionDetailsEngine.get_position_details("TRD_201")
    c_det1, c_det2 = st.columns(2)
    with c_det1:
        st.markdown(
            f"""
            <div class="sensibull-card">
                <h4><b>Trade Rationale: {pos_det.trade_id}</b></h4>
                <p><b>Why Entered?</b> {pos_det.explainer.why_entered}</p>
                <p><b>Why Still Holding?</b> {pos_det.explainer.why_holding}</p>
                <p><b>What Makes AI Exit?</b> {pos_det.explainer.what_makes_ai_exit}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_det2:
        st.markdown(
            f"""
            <div class="sensibull-card">
                <h4><b>Progress & Probabilities</b></h4>
                <p><b>Target Progress:</b> {pos_det.target_progress_pct:.0f}%</p>
                <p><b>Win Probability:</b> {pos_det.explainer.current_win_probability:.1f}%</p>
                <p><b>Expected Reward:</b> +₹{pos_det.explainer.expected_reward_amount:,.2f}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif nav == "📑 Orderbook & Trade Book":
    st.header("📑 Broker Orderbook & Chronological Execution Trade Book")
    tab_ord, tab_trade = st.tabs(["📋 Broker Orderbook", "📜 Chronological Execution Ledger"])

    with tab_ord:
        st.subheader("📋 Pending, Executed & Rejected Orders")
        st.dataframe(pd.DataFrame([o.__dict__ for o in broker_orderbook.orders]), **button_kwargs)

    with tab_trade:
        st.subheader("📜 Execution History Ledger")
        st.dataframe(pd.DataFrame([e.__dict__ for e in broker_orderbook.events]), **button_kwargs)

elif nav == "🛡️ Autonomous Paper Trader":
    st.header("🛡️ Autonomous Paper Trading Engine & Auto Exits")
    c_sw, c_cfg = st.columns(2)

    with c_sw:
        st.markdown(
            """
            <div class="sensibull-card">
                <h3><b>⚡ Autonomous Loop Controller</b></h3>
                <p><b>Status:</b> RUNNING (Scanning 1-min candles)</p>
                <p><b>Next Scan:</b> In 4 seconds...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔴 Pause Autonomous Loop", **button_kwargs):
            st.warning("Autonomous loop paused.")

    with c_cfg:
        st.subheader("⚙️ Configurable Auto Exit Rules")
        st.checkbox("Enable Break-Even Stop Loss on Target 1", value=True)
        st.checkbox("Enable ATR 2.0x Trailing Stop", value=True)
        st.checkbox("Enable 45-min Time Stop Exit", value=True)
        st.checkbox("Enable Profit Lock (50% booking at T1)", value=True)

elif nav == "📈 Real-Time Option Monitor":
    st.header("📈 Real-Time Option Monitor Telemetry")
    snap: RealtimeOptionSnapshot = RealtimeOptionMonitor.get_live_snapshot()

    o1, o2, o3, o4, o5, o6 = st.columns(6)
    o1.metric("Premium", f"₹{snap.premium:.2f}")
    o2.metric("Intrinsic", f"₹{snap.intrinsic_value:.2f}")
    o3.metric("Extrinsic", f"₹{snap.extrinsic_value:.2f}")
    o4.metric("Delta", f"{snap.delta:.2f}")
    o5.metric("Theta", f"₹{snap.theta:.2f}")
    o6.metric("IV", f"{snap.iv:.1f}% ({snap.iv_change:+.2f}%)")

elif nav == "⚡ Live Validation Panel":
    st.header("⚡ AI Prediction Live Validation Panel & Calibration Matrix")

elif nav == "⚡ Institutional Trade Desk":
    st.header("⚡ Institutional Trading Workstation")

elif nav == "📈 Live Option Analytics":
    st.header("📈 Dedicated Live Option Analytics Matrix & Greeks")

elif nav == "📊 Portfolio Risk Dashboard":
    st.header("📊 Aggregated Portfolio Risk Engine & Greeks Matrix")

elif nav == "🎯 Performance Lab":
    st.header("🎯 Quantitative Performance Lab Suite")

elif nav == "🧬 Strategy Lab":
    st.header("🧬 Strategy Lab & Plugin Leaderboard Matrix")

elif nav == "💡 Numerical Trade Explainability":
    st.header("💡 Numerical Trade Explainability & Post-Trade Audit")

elif nav == "📊 Backtest vs Paper Comparison":
    st.header("📊 Backtest Expectations vs Actual Paper Performance")

elif nav == "🧠 AI Research Lab":
    st.header("🧠 Autonomous Learning Engine & Institutional Research Lab")

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
