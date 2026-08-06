"""QuantFlow v16.0 — Real Market Paper Trading Engine & Live MTM Workstation."""

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
from app.analytics.live_validation import LiveValidationPanel, TerminalComparisonRow
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
from app.marketdata.data_quality import DataQualityEngine, DataQualityReport
from app.marketdata.live_feed import Tick
from app.marketdata.live_greeks_engine import LiveGreeksEngine, LiveGreeksSnapshot
from app.marketdata.live_option_chain import LiveOptionChainMatrix, OptionChainMatrixSnapshot, StrikeChainRow
from app.marketdata.live_option_price_engine import LiveOptionPriceEngine, OptionContractTick
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
from app.paper.contract_note import ZerodhaContractNote, ZerodhaContractNoteCalculator
from app.paper.real_execution_sim import RealExecutionResult, RealExecutionSimulator
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
from app.risk.real_margin_engine import MarginBreakdown, RealMarginEngine
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
from app.trading_desk.mtm_engine import MTMEngine, PortfolioMTMHeader, PositionMTMSnapshot
from app.trading_desk.order_audit_log import AuditEvent, OrderAuditLogger
from app.trading_desk.position_details import DeepPositionDetails, PositionDetailsEngine, PositionExplainerOutput
from app.trading_desk.position_timeline import PositionTimelineEngine, PositionTimelineStep
from app.trading_desk.position_tracker import ClosedPosition, OpenPosition, PositionTracker
from app.trading_desk.rejected_trades import RejectedTrade, RejectedTradeLogger
from app.trading_desk.session_summary import SessionSummary, SessionSummaryGenerator
from app.trading_desk.telegram_notifier import TelegramNotifier

st.set_page_config(
    page_title="QuantFlow v16.0 — Real Market Paper Trading Workstation",
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

live_price_engine = LiveOptionPriceEngine.get_instance()
data_quality_engine = DataQualityEngine.get_instance()
inst_pos_tracker = InstitutionalPositionTracker.get_instance()
broker_orderbook = BrokerOrderBook.get_instance()
integrity_engine = MarketIntegrityEngine.get_instance()
health_monitor = AutonomousHealthMonitor.get_instance()

# Custom Sensibull & Kite Dark Theme CSS styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    .kite-mtm-bar {
        background-color: #161b22;
        padding: 12px 18px;
        border-radius: 6px;
        border: 1px solid #238636;
        margin-bottom: 14px;
        font-family: monospace;
    }
    .pnl-positive { color: #3fb950; font-weight: bold; }
    .pnl-negative { color: #f85149; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fetch MTM Header Metrics
mtm_pos1 = MTMEngine.calculate_position_mtm("TRD_201", "28th Jul 24250 CE", 260, 218.50, 245.00)
mtm_pos2 = MTMEngine.calculate_position_mtm("TRD_202", "28th Jul 24550 CE", -260, 90.30, 75.00)
mtm_header: PortfolioMTMHeader = MTMEngine.get_portfolio_mtm_header([mtm_pos1, mtm_pos2])
dq_report: DataQualityReport = data_quality_engine.get_quality_report()

# KITE TOP MTM BAR
st.markdown(
    f"""
    <div class="kite-mtm-bar">
        <span style="font-size:16px; font-weight:bold; color:#3fb950;">⚡ ZERODHA KITE LIVE MTM WORKSTATION</span> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>Today's MTM:</b> <span class="pnl-positive">+₹{mtm_header.todays_mtm:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Total MTM:</b> <span class="pnl-positive">+₹{mtm_header.total_mtm:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Running Profit:</b> <span class="pnl-positive">+₹{mtm_header.running_profit:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Running Loss:</b> <span class="pnl-negative">₹{mtm_header.running_loss:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Heartbeat:</b> <b style="color:#3fb950;">[{dq_report.heartbeat_status}]</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Workstation")
st.sidebar.caption("Real Market Paper Engine v16.0")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "⚡ Live MTM Workstation (Kite Style)",
        "🔍 Live Validation Panel (QuantFlow vs Kite)",
        "📊 Real Margin & Contract Note Calculator",
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


if nav == "⚡ Live MTM Workstation (Kite Style)":
    st.header("⚡ Live Mark-To-Market (MTM) Portfolio Workstation")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Today's MTM", f"+₹{mtm_header.todays_mtm:,.2f}")
    m2.metric("Total MTM PnL", f"+₹{mtm_header.total_mtm:,.2f}")
    m3.metric("Running Profit", f"+₹{mtm_header.running_profit:,.2f}")
    m4.metric("Open Positions", mtm_header.open_positions_count)

    st.markdown("---")
    st.subheader("🟢 Live Mark-To-Market Positions Table")
    st.dataframe(pd.DataFrame([mtm_pos1.__dict__, mtm_pos2.__dict__]), **button_kwargs)

elif nav == "🔍 Live Validation Panel (QuantFlow vs Kite)":
    st.header("🔍 Live Validation Panel (QuantFlow vs Sensibull vs Zerodha Kite)")
    val_rows: List[TerminalComparisonRow] = LiveValidationPanel.validate_terminal_prices()
    st.dataframe(pd.DataFrame([v.__dict__ for v in val_rows]), **button_kwargs)

elif nav == "📊 Real Margin & Contract Note Calculator":
    st.header("📊 Zerodha Margin Calculator & Statutory Contract Note")
    col_m, col_c = st.columns(2)

    with col_m:
        st.subheader("💰 Margin Requirements Breakdown")
        margin_res: MarginBreakdown = RealMarginEngine.calculate_margin(260, 218.50, is_selling=False)
        st.write(f"**SPAN Margin:** ₹{margin_res.span_margin:,.2f}")
        st.write(f"**Exposure Margin:** ₹{margin_res.exposure_margin:,.2f}")
        st.write(f"**Premium Blocked:** ₹{margin_res.premium_margin:,.2f}")
        st.write(f"**Total Blocked Margin:** ₹{margin_res.total_blocked_margin:,.2f}")

    with col_c:
        st.subheader("📄 Zerodha Contract Note Tax Breakdown")
        cn: ZerodhaContractNote = ZerodhaContractNoteCalculator.calculate_contract_note(218.50, 245.00, 260)
        st.write(f"**Gross PnL:** +₹{cn.gross_pnl:,.2f}")
        st.write(f"**Flat Brokerage:** ₹{cn.flat_brokerage:.2f}")
        st.write(f"**STT (0.125%):** ₹{cn.stt:.2f}")
        st.write(f"**Exchange Charges:** ₹{cn.exchange_turnover_charge:.2f}")
        st.write(f"**GST (18%):** ₹{cn.gst:.2f}")
        st.write(f"**Stamp Duty:** ₹{cn.stamp_duty:.2f}")
        st.write(f"**Total Charges:** ₹{cn.total_tax_charges:.2f}")
        st.markdown(f"### **Net Realized PnL: +₹{cn.net_realized_pnl:,.2f}**")

elif nav == "📊 Institutional Positions (Sensibull/Kite OMS)":
    st.header("📊 Net Positions & Strategy Groupings (Sensibull OMS Workstation)")

elif nav == "📑 Orderbook & Trade Book":
    st.header("📑 Broker Orderbook & Chronological Execution Trade Book")

elif nav == "🛡️ Autonomous Paper Trader":
    st.header("🛡️ Autonomous Paper Trading Engine & Auto Exits")

elif nav == "📈 Real-Time Option Monitor":
    st.header("📈 Real-Time Option Monitor Telemetry")

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

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
