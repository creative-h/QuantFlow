"""QuantFlow v16.0 — Sensibull Draft Portfolios & Institutional Workstation."""

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
    page_title="QuantFlow — Sensibull Draft Portfolios Workstation",
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

# Sensibull Draft Portfolios Custom CSS styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    .sensibull-brand {
        font-size: 20px;
        font-weight: 800;
        color: #ff6838;
        font-family: 'Inter', sans-serif;
    }
    .sensibull-panel {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .sensibull-card-title {
        color: #8b949e;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .pnl-positive { color: #3fb950; font-weight: bold; }
    .pnl-negative { color: #f85149; font-weight: bold; }
    .badge-buy { background-color: #1f6beb; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-sell { background-color: #d29922; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-closed { background-color: #484f58; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fetch MTM Header Metrics
mtm_pos1 = MTMEngine.calculate_position_mtm("TRD_201", "28th Jul 24250 CE", 260, 218.50, 245.00)
mtm_pos2 = MTMEngine.calculate_position_mtm("TRD_202", "28th Jul 24550 CE", -260, 90.30, 75.00)
mtm_header: PortfolioMTMHeader = MTMEngine.get_portfolio_mtm_header([mtm_pos1, mtm_pos2])
dq_report: DataQualityReport = data_quality_engine.get_quality_report()

# Top Brand Nav
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 16px;">
        <div>
            <span class="sensibull-brand">⚡ SENSIBULL</span> &nbsp;<span style="color:#8b949e;">/ Draft Portfolios (AI Autonomous Workstation)</span>
        </div>
        <div>
            <span style="background-color:#1f6beb; color:white; padding:4px 10px; border-radius:4px; font-size:12px; font-weight:bold;">Drafts Mode</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Workstation")
st.sidebar.caption("Sensibull Draft Portfolios OMS")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "📊 Institutional Positions (Sensibull Drafts)",
        "⚡ Live MTM Workstation (Kite Style)",
        "🔍 Live Validation Panel (QuantFlow vs Kite)",
        "📊 Real Margin & Contract Note Calculator",
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


if nav == "📊 Institutional Positions (Sensibull Drafts)":
    c_left_side, c_main_side = st.columns([1, 3.2])

    # LEFT SIDEBAR SUMMARY PANEL (Matching Sensibull Drafts Sidebar)
    with c_left_side:
        st.markdown(
            """
            <div class="sensibull-panel">
                <div style="font-size:14px; font-weight:bold; margin-bottom:12px;">Drafts Mode — 5 of 5 Strategies</div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <div><span class="sensibull-card-title">Total P&L</span><br/><span class="pnl-negative" style="font-size:16px;">-₹26,811</span></div>
                    <div><span class="sensibull-card-title">Unbooked P&L</span><br/><span class="pnl-negative" style="font-size:16px;">-₹33,332</span></div>
                    <div><span class="sensibull-card-title">Booked P&L</span><br/><span class="pnl-positive" style="font-size:16px;">+₹6,522</span></div>
                </div>
                <div style="font-size:12px; color:#8b949e;">Total Decay: <b>0</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.checkbox("Show closed positions", value=True)
        st.markdown("<b>Select Strategies:</b>", unsafe_allow_html=True)
        st.checkbox("✓ 28 July (4 of 4 Positions)  -30,339", value=True)
        st.checkbox("✓ 14th July (2 of 2 Positions)  -4,482", value=True)
        st.checkbox("✓ 7th July expiry (2 of 2 Positions)  -2,532", value=True)

    # RIGHT MAIN AREA (Matching Sensibull Draft Portfolios Table & Actions)
    with c_main_side:
        st.markdown(
            """
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="font-size:15px; font-weight:bold;">Portfolios > AI test and learn</div>
                <div>
                    <button style="background-color:#1f6beb; color:white; border:none; padding:6px 14px; border-radius:6px; font-weight:bold; cursor:pointer;">+ Create New Strategy</button>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Strategy Group Card Header
        st.markdown(
            """
            <div class="sensibull-panel">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div>
                        <span style="font-size:18px; font-weight:bold; color:#58a6ff;">📅 28 July Expiry</span>
                        <span style="font-size:12px; color:#8b949e; margin-left:10px;">4 of 4 Positions</span>
                    </div>
                    <div>
                        <span><b>Total P&L:</b> <span class="pnl-negative">-₹30,339.00</span></span> &nbsp;&nbsp;|&nbsp;&nbsp;
                        <span><b>Unbooked:</b> <span class="pnl-negative">-₹33,332.00</span></span> &nbsp;&nbsp;|&nbsp;&nbsp;
                        <span><b>Booked:</b> <span class="pnl-positive">+₹2,993.00</span></span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tabs matching Sensibull
        t_net, t_orders, t_greeks = st.tabs(["Net Positions", "Orderbook", "Greeks"])

        with t_net:
            st.markdown("<b>NIFTY 24,559.30 <span class='pnl-negative'>-0.31%</span></b> &nbsp;&nbsp;|&nbsp;&nbsp; Breakeven: -- &nbsp;|&nbsp; Max Profit: -- &nbsp;|&nbsp; Max Loss: --", unsafe_allow_html=True)
            st.markdown("<br/>", unsafe_allow_html=True)

            # Construct exact Sensibull Table Data
            sensibull_rows = [
                {"Select": "☐", "Side": "[-] Closed", "Instrument": "28th Jul 24050 CE", "Qty": 0, "Avg Price": "₹0.00", "LTP": "₹0.25", "Total P&L": "+₹6,451.00", "Unbooked P&L": "₹0.00", "Booked P&L": "+₹6,451.00"},
                {"Select": "☑", "Side": "[B] Buy", "Instrument": "28th Jul 24250 CE", "Qty": 260, "Avg Price": "₹218.50", "LTP": "₹0.10", "Total P&L": "-₹56,784.00", "Unbooked P&L": "-₹56,784.00", "Booked P&L": "₹0.00"},
                {"Select": "☐", "Side": "[-] Closed", "Instrument": "28th Jul 24350 CE", "Qty": 0, "Avg Price": "₹0.00", "LTP": "₹0.25", "Total P&L": "-₹3,458.00", "Unbooked P&L": "₹0.00", "Booked P&L": "-₹3,458.00"},
                {"Select": "☑", "Side": "[S] Sell", "Instrument": "28th Jul 24550 CE", "Qty": -260, "Avg Price": "₹90.30", "LTP": "₹0.10", "Total P&L": "+₹23,452.00", "Unbooked P&L": "+₹23,452.00", "Booked P&L": "₹0.00"},
            ]
            df_sensibull = pd.DataFrame(sensibull_rows)
            st.dataframe(df_sensibull, **button_kwargs)

            # Sensibull Action Buttons Bar
            c_act1, c_act2, c_act3, c_act4, c_act5 = st.columns(5)
            c_act1.button("↗ Open in Builder", **button_kwargs)
            c_act2.button("+ Add Orders", **button_kwargs)
            c_act3.button("🚪 Exit Orders (2)", **button_kwargs)
            c_act4.button("✏️ Edit (4)", **button_kwargs)
            c_act5.button("🗑️ Delete (4)", **button_kwargs)

        with t_orders:
            st.subheader("📋 Orderbook Ledger")
            st.dataframe(pd.DataFrame([o.__dict__ for o in broker_orderbook.orders]), **button_kwargs)

        with t_greeks:
            st.subheader("📊 Aggregated Strategy Greeks")
            st.write("**Strategy Delta:** +45.2 | **Strategy Gamma:** +0.85 | **Strategy Theta:** -₹1,250.00 | **Strategy Vega:** +₹620.00")

elif nav == "⚡ Live MTM Workstation (Kite Style)":
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
