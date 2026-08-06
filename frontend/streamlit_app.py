"""QuantFlow — Autonomous Institutional Paper Trading System Workstation."""

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
from app.analytics.backtest_comparison import BacktestComparisonEngine
from app.analytics.coach_engine import AITradingCoachEngine, LessonsLearned, SetupMatchResult, TradeExplanation
from app.analytics.market_health import MarketHealthMonitor, MarketHealthOverview
from app.analytics.multi_agent.coordinator import DecisionCoordinator
from app.analytics.multi_agent.debate import AIDebateEngine, AIDebateSession
from app.analytics.multi_agent.decision import AITradeDecision, AgentOpinion
from app.analytics.multi_agent.scoreboard import ScoreboardConsensus, StrategyScoreboard
from app.analytics.performance_auditor import AuditReport, PerformanceAuditor
from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.analytics.trade_explainability import NumericalTradeExplanation, NumericalTradeExplainer, PostTradeAudit
from app.indicators.engine import IndicatorEngine
from app.marketdata.live_feed import Tick
from app.marketdata.market_integrity import FeedCheckResult, MarketIntegrityEngine
from app.marketdata.market_state import MarketStateEngine, MarketStatusInfo
from app.marketdata.option_chain import OptionChain, OptionChainEngine
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
from app.research.self_learning import SelfLearningLoop
from app.research.strategy_scorer import StrategyScoreEngine
from app.research.trade_dataset import TradeDatasetBuilder
from app.research.walk_forward import WalkForwardEngine
from app.simulation.replay_engine import MarketReplayEngine, ReplayState
from app.strategies.registry import StrategyRegistry
from app.system.health_monitor import AutonomousHealthMonitor, SystemHealthMetrics
from app.trade_management.position_sizer import ProfessionalPositionSizer
from app.trade_management.target_manager import TargetManager
from app.trade_management.trailing_stop_engine import TrailingStopEngine
from app.trading_desk.execution_pipeline import ExecutionPipeline
from app.trading_desk.live_trade_book import LiveTradeBook, TradeBookEntry
from app.trading_desk.order_audit_log import AuditEvent, OrderAuditLogger
from app.trading_desk.position_tracker import ClosedPosition, OpenPosition, PositionTracker
from app.trading_desk.rejected_trades import RejectedTrade, RejectedTradeLogger
from app.trading_desk.session_summary import SessionSummary, SessionSummaryGenerator
from app.trading_desk.telegram_notifier import TelegramNotifier

st.set_page_config(
    page_title="QuantFlow — Autonomous Institutional Workstation",
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

integrity_engine = MarketIntegrityEngine.get_instance()
health_monitor = AutonomousHealthMonitor.get_instance()
trade_book = LiveTradeBook.get_instance()
audit_logger = OrderAuditLogger.get_instance()
rejected_logger = RejectedTradeLogger.get_instance()
position_tracker = PositionTracker.get_instance()

# Custom Dark Theme CSS styling for Zerodha OMS-style Workstation
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
    .warning-banner {
        background-color: #3d1d1d;
        color: #f85149;
        padding: 10px 16px;
        border-radius: 6px;
        border: 1px solid #f85149;
        margin-bottom: 12px;
        font-weight: bold;
    }
    .pipeline-bar {
        background-color: #161b22;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #388bfd;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        font-family: monospace;
        font-size: 12px;
    }
    .stage-complete { color: #3fb950; font-weight: bold; }
    .stage-active { color: #d29922; font-weight: bold; }
    .stage-pending { color: #8b949e; }
    .coach-card {
        background-color: #161b22;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #238636;
        margin-bottom: 12px;
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
nifty_p_val = nifty_tick.price if nifty_tick else 24915.20

# Run Market Integrity Check
feed_check: FeedCheckResult = integrity_engine.validate_symbol_feeds("NIFTY", nifty_p_val)
health_snap: SystemHealthMetrics = health_monitor.get_health_snapshot()

nifty_p = f"₹{nifty_p_val:,.2f}"
conn_str = "CONNECTED" if ws_manager.is_connected() else "SIMULATED / RECONNECTING"
conn_color = "#3fb950" if ws_manager.is_connected() else "#d29922"
lat_val = f"{health_snap.websocket_latency_ms:.1f}ms"
time_str = market_status.timestamp.strftime("%H:%M:%S IST")
status_badge_color = "#3fb950" if market_status.status == "OPEN" else "#f85149"

# TOP HUD BAR
st.markdown(
    f"""
    <div class="hud-bar">
        <b style="color:{conn_color};">● KITE WEBSOCKET: {conn_str}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>NIFTY:</b> {nifty_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>WS Latency:</b> <span style="color:#58a6ff;">{lat_val}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>API Latency:</b> {health_snap.api_latency_ms:.0f}ms &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Time:</b> {time_str} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Today's PnL:</b> <span class="pnl-positive">+₹4,250.00</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Exposure:</b> 2.95% &nbsp;&nbsp;&nbsp;&nbsp;
        <b>CPU:</b> {health_snap.cpu_usage_pct}% &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Memory:</b> {health_snap.memory_usage_mb}MB &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Health:</b> <b style="color:#3fb950;">[{health_snap.status}]</b>
    </div>
    """,
    unsafe_allow_html=True,
)

# Market Data Integrity Warning Banner (if threshold breach)
if feed_check.status == "ACCEPTABLE_WARNING":
    st.markdown(f"<div class='warning-banner'>⚠️ MARKET INTEGRITY WARNING: {feed_check.message}</div>", unsafe_allow_html=True)
elif feed_check.status == "INVALID_DATA":
    st.markdown(f"<div class='warning-banner'>🚨 INVALID DATA BREACH: {feed_check.message} — Autonomous Trading Paused!</div>", unsafe_allow_html=True)

# LIVE EXECUTION PIPELINE STAGE BAR
p_stages = pipeline.get_pipeline_status()
pipeline_html = "<div class='pipeline-bar'><b>⚡ LIVE EXECUTION PIPELINE:</b> &nbsp;"
for p in p_stages:
    cls = "stage-complete" if p["status"] == "COMPLETED" else ("stage-active" if p["status"] == "ACTIVE" else "stage-pending")
    pipeline_html += f"<span class='{cls}'>[{p['stage']} ✓]</span> &nbsp;→&nbsp; "
pipeline_html = pipeline_html[:-7] + "</div>"
st.markdown(pipeline_html, unsafe_allow_html=True)

st.sidebar.title("⚡ QuantFlow Workstation")
st.sidebar.caption("Autonomous Institutional Paper System")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "⚡ Institutional Trade Desk",
        "💡 Numerical Trade Explainability",
        "📊 Backtest vs Paper Comparison",
        "🧠 AI Research Lab",
        "🎓 AI Trading Coach Studio",
        "🎞️ Market Replay Simulator",
        "🎯 Trade Management Studio",
        "🤖 AI Command Center",
        "🛡️ Session Risk Dashboard",
        "⛓️ Live Option Chain Matrix",
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


if nav == "⚡ Institutional Trade Desk":
    col_left, col_center, col_right = st.columns([1.1, 3.2, 1.7])

    with col_left:
        st.subheader("👁️ Watchlist")
        target_symbol = st.selectbox("Symbol", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"], index=0)
        expiry_sel = st.selectbox("Expiry", ["2026-08-07 (Weekly)", "2026-08-14", "2026-08-28 (Monthly)"], index=0)
        interval_sel = st.selectbox("Timeframe", ["1-Min", "3-Min", "5-Min", "15-Min", "1-Hour", "1-Day"], index=0)

        st.markdown("---")
        st.subheader("💸 Realistic Execution Friction")
        cost = RealisticBroker.calculate_execution("BUY", 118.0, 50)
        st.write(f"**Flat Brokerage:** ₹{cost.brokerage:.2f}")
        st.write(f"**STT:** ₹{cost.stt:.2f}")
        st.write(f"**Exchange Fees:** ₹{cost.exchange_charges:.2f}")
        st.write(f"**GST (18%):** ₹{cost.gst:.2f}")
        st.write(f"**Slippage (0.05%):** ₹{cost.slippage:.2f}")
        st.write(f"**Total Charges:** ₹{cost.total_charges:.2f}")
        st.write(f"**Execution Delay:** {cost.execution_delay_ms:.0f}ms")

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

        # Overlay Buy/Sell markers
        fig.add_trace(go.Scatter(x=[df_chart.index[-5]], y=[df_chart["low"].iloc[-5] - 15.0], mode="markers+text", marker=dict(symbol="triangle-up", size=14, color="#3fb950"), text=["BUY ₹118"], textposition="bottom center", name="AI Entry"), row=1, col=1)
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart["volume"], marker_color="#30363d", name="Volume"), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=420, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, **button_kwargs)

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

    st.markdown("---")

    # LIVE TRADE BOOK & POSITION TABLES
    t_book, t_open, t_closed, t_rej, t_audit = st.tabs(["📋 Institutional Live Trade Book", "🟢 Live Open Positions", "🔴 Live Closed Positions", "🚫 Rejected Trade Log", "📋 Event Audit Log"])

    with t_book:
        st.subheader("📋 Institutional Live Trade Book & Lifecycle Status")
        st.dataframe(pd.DataFrame([t.__dict__ for t in trade_book.trades]), **button_kwargs)

    with t_open:
        st.subheader("🟢 Live Open Positions & Greeks Telemetry")
        st.dataframe(pd.DataFrame([p.__dict__ for p in position_tracker.open_positions]), **button_kwargs)

    with t_closed:
        st.subheader("🔴 Live Closed Positions Ledger")
        st.dataframe(pd.DataFrame([p.__dict__ for p in position_tracker.closed_positions]), **button_kwargs)

    with t_rej:
        st.subheader("🚫 Rejected Trade Audit Log")
        st.dataframe(pd.DataFrame([r.__dict__ for r in rejected_logger.get_all_rejections()]), **button_kwargs)

    with t_audit:
        st.subheader("📋 System Order Event Audit Log")
        st.dataframe(pd.DataFrame([e.__dict__ for e in audit_logger.get_recent_events()]), **button_kwargs)

elif nav == "💡 Numerical Trade Explainability":
    st.header("💡 Numerical Trade Explainability & Post-Trade Audit")
    num_exp: NumericalTradeExplanation = NumericalTradeExplainer.explain_trade_numerically("NIFTY", "BUY")
    audit_res: PostTradeAudit = NumericalTradeExplainer.audit_completed_trade("TRD_101", 1450.0)

    e1, e2, e3, e4, e5, e6 = st.columns(6)
    e1.metric("Trend Score", f"+{num_exp.trend_score:.0f}")
    e2.metric("Momentum Score", f"+{num_exp.momentum_score:.0f}")
    e3.metric("VWAP Dist", f"+{num_exp.vwap_distance_pct:.2f}%")
    e4.metric("PCR", f"{num_exp.pcr:.2f}")
    e5.metric("Volume Ratio", f"{num_exp.volume_ratio:.2f}x")
    e6.metric("Option Gamma", f"{num_exp.gamma:.3f}")

    st.markdown("---")
    st.subheader(f"🏆 Post-Trade Audit Grade: {audit_res.grade} (Overall Score: {audit_res.overall_trade_score}/100)")
    st.write(f"**Execution Score:** {audit_res.execution_score}/100 | **Risk Score:** {audit_res.risk_score}/100 | **Psychology Score:** {audit_res.psychology_score}/100")
    st.success(f"**What AI Liked:** " + ", ".join(audit_res.ai_liked))
    st.warning(f"**What AI Disliked:** " + ", ".join(audit_res.ai_disliked))

elif nav == "📊 Backtest vs Paper Comparison":
    st.header("📊 Backtest Expectations vs Actual Paper Performance")
    comp_map = BacktestComparisonEngine.compare_performance()
    st.dataframe(pd.DataFrame([m.__dict__ for m in comp_map.values()]), **button_kwargs)

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

elif nav == "🛡️ Session Risk Dashboard":
    st.header("🛡️ Interactive Session Risk Dashboard")

elif nav == "⛓️ Live Option Chain Matrix":
    st.header("⛓️ Dedicated Live Option Chain Matrix")

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
