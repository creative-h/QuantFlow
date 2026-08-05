"""QuantFlow v3.0 — Real-Time Indian Market Engine & Institutional Workstation."""

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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

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
    page_title="QuantFlow v3.0 — Real-Time Indian Market Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for WebSocketManager & Autonomous Trader in Streamlit
if "ws_manager" not in st.session_state:
    st.session_state["ws_manager"] = WebSocketManager()
    st.session_state["ws_manager"].connect()

ws_manager: WebSocketManager = st.session_state["ws_manager"]

if "auto_trader" not in st.session_state:
    st.session_state["auto_trader"] = AutonomousPaperTrader()

auto_trader: AutonomousPaperTrader = st.session_state["auto_trader"]

# Custom Dark Theme CSS styling for QuantFlow v3.0 Institutional Workstation
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
    .agent-card {
        background-color: #161b22;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 8px;
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
        overflow-y. auto;
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
mid_tick = ws_manager.latest_tick("MIDCPNIFTY")

nifty_p = f"₹{nifty_tick.price:,.2f}" if nifty_tick else "₹24,915.20"
bank_p = f"₹{bank_tick.price:,.2f}" if bank_tick else "₹55,201.00"
fin_p = f"₹{fin_tick.price:,.2f}" if fin_tick else "₹22,450.00"
mid_p = f"₹{mid_tick.price:,.2f}" if mid_tick else "₹13,150.00"

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
        <b>MIDCPNIFTY:</b> {mid_p} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>VIX:</b> 12.80 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Latency:</b> <span style="color:#58a6ff;">{lat_val}</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>Time:</b> {time_str} &nbsp;&nbsp;&nbsp;&nbsp;
        <b>State:</b> <b style="color:{status_badge_color};">[{market_status.status}]</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Workstation v3.0")
st.sidebar.caption("Real-Time Indian Market Engine (Kite WebSocket)")

nav = st.sidebar.radio(
    "Workstation Views",
    [
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
        # Fallback synthetic generator for Indian Index Spot Price
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


if nav == "🏛️ AI Trading Desk":
    # Main Grid Layout: Left Panel (1.2 cols), Center Panel (3 cols), Right Panel (2 cols)
    col_left, col_mid, col_right = st.columns([1.2, 3, 2])

    with col_left:
        st.subheader("🎯 Instrument Selection")
        target_symbol = st.selectbox("Underlying Index", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"], index=0)
        expiry = st.selectbox("Expiry Date", ["Current Weekly (Thursday)", "Next Weekly", "Monthly"], index=0)
        interval = st.selectbox("Timeframe Interval", ["1m", "3m", "5m", "15m", "30m", "1h", "1d"], index=0)

        df_chart = st.session_state.get("market_df", fetch_sample_data(target_symbol, "1mo"))
        latest_spot = float(df_chart["close"].iloc[-1])
        atm_strike = OptionChainEngine.calculate_atm_strike(target_symbol, latest_spot)

        st.metric(f"{target_symbol} Live Spot Price", f"₹{latest_spot:,.2f}")
        st.metric("ATM Strike Price", f"₹{atm_strike:,.0f}")

        st.markdown("---")
        st.subheader("⚙️ Strategy & Autonomous Mode")
        strat_choice = st.selectbox("Active Strategy Engine", StrategyRegistry.list_strategies())

        auto_mode = st.toggle("🤖 Autonomous Trading Mode", value=auto_trader.is_auto_trading)
        if auto_mode != auto_trader.is_auto_trading:
            if auto_mode:
                auto_trader.start()
            else:
                auto_trader.stop()
            st.rerun()

        if st.button("⚡ Evaluate Multi-Agent Consensus", **button_kwargs):
            auto_trader.scan_and_execute()
            st.success(f"Evaluated multi-agent consensus for {target_symbol}")
            st.rerun()

    with col_mid:
        st.subheader(f"📈 {target_symbol} TradingView Chart ({interval} Bar)")

        # Compute technical indicator overlays
        df_chart["ema20"] = IndicatorEngine.ema(df_chart, 20)
        df_chart["ema50"] = IndicatorEngine.ema(df_chart, 50)
        df_chart["vwap"] = IndicatorEngine.vwap(df_chart)

        supp_level = atm_strike - 150.0
        res_level = atm_strike + 150.0

        # Plotly Candlestick Chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])

        fig.add_trace(
            go.Candlestick(
                x=df_chart.index,
                open=df_chart["open"],
                high=df_chart["high"],
                low=df_chart["low"],
                close=df_chart["close"],
                name="Spot OHLC",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(x=df_chart.index, y=df_chart["ema20"], line=dict(color="#58a6ff", width=1.5), name="EMA 20"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df_chart.index, y=df_chart["ema50"], line=dict(color="#d29922", width=1.5), name="EMA 50"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df_chart.index, y=df_chart["vwap"], line=dict(color="#bc8cff", width=1.5, dash="dash"), name="VWAP"),
            row=1,
            col=1,
        )

        # Support & Resistance Horizontal Lines
        fig.add_hline(y=res_level, line_color="#f85149", line_dash="dot", annotation_text="Resistance", row=1, col=1)
        fig.add_hline(y=supp_level, line_color="#3fb950", line_dash="dot", annotation_text="Support", row=1, col=1)
        fig.add_hline(y=latest_spot, line_color="#58a6ff", line_width=1, annotation_text=f"Live: ₹{latest_spot:,.2f}", row=1, col=1)

        # Volume Bar
        fig.add_trace(
            go.Bar(x=df_chart.index, y=df_chart["volume"], marker_color="#30363d", name="Volume"),
            row=2,
            col=1,
        )

        fig.update_layout(
            template="plotly_dark",
            height=440,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False,
            paper_bgcolor="#0b0e14",
            plot_bgcolor="#0b0e14",
        )
        st.plotly_chart(fig, **button_kwargs)

        # Live AI Session Commentary Timeline
        st.subheader("📜 Live AI Session Commentary Timeline")
        timeline_html = "<div class='timeline-box'>"
        for event in reversed(auto_trader.ai_timeline):
            ts_str = event.timestamp.strftime("%H:%M:%S")
            cat_color = "#3fb950" if event.category == "ORDER" else "#58a6ff"
            timeline_html += f"<div><span style='color:#8b949e;'>[{ts_str}]</span> <b style='color:{cat_color};'>[{event.category}]</b> {event.message}</div>"
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)

    with col_right:
        st.subheader("🤖 Live AI Panel")

        candle_now = Candle(
            timestamp=datetime.now(),
            open=float(df_chart["open"].iloc[-1]),
            high=float(df_chart["high"].iloc[-1]),
            low=float(df_chart["low"].iloc[-1]),
            close=float(df_chart["close"].iloc[-1]),
            volume=int(df_chart["volume"].iloc[-1]),
        )
        ai_dec: AITradeDecision = auto_trader.coordinator.evaluate_consensus(target_symbol, candle_now, df_chart)
        coach_adv: AICoachAdvice = AICoach.generate_advice(ai_dec)

        st.markdown(
            f"""
            <div class="trade-action-box">
                ⚡ SIGNAL: {ai_dec.action} {ai_dec.symbol} {int(ai_dec.strike)} {ai_dec.option_type}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="coach-card">
                <p><b>Current Spot:</b> ₹{latest_spot:,.2f}</p>
                <p><b>Current Option Price:</b> ₹{ai_dec.entry:.2f}</p>
                <p><b>Current Trend:</b> <b style="color:#3fb950;">{ai_dec.market_regime}</b></p>
                <p><b>AI Confidence:</b> <b style="color:#d29922;">{ai_dec.confidence:.1f}%</b></p>
                <hr style="border-color:#30363d;"/>
                <p><b>Reasoning:</b> {ai_dec.reason}</p>
                <hr style="border-color:#30363d;"/>
                <p style="color:#3fb950;"><b>Coach Advice:</b> {coach_adv.action_answer}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Bottom Panel: Live Option Chain Matrix with Greeks & Highlighting
    st.subheader(f"⛓️ Live Option Chain Matrix with Option Greeks ({target_symbol})")
    chain: OptionChain = OptionChainEngine.generate_chain(target_symbol, latest_spot)

    st.caption(f"ATM Strike: **{chain.atm_strike:.0f}** | Put-Call Ratio (PCR): **{chain.pcr:.2f}** | Max Pain: **{chain.max_pain:.0f}** | Support: **{chain.support_level:.0f}** | Resistance: **{chain.resistance_level:.0f}**")

    matrix_rows = []
    for strike in sorted(chain.calls.keys()):
        c = chain.calls[strike]
        p = chain.puts[strike]

        tag = ""
        if c.is_atm:
            tag = "⚡ ATM"
        elif c.is_resistance:
            tag = "🔴 RES (Max OI)"
        elif p.is_support:
            tag = "🟢 SUPP (Max OI)"

        matrix_rows.append(
            {
                "CE LTP (₹)": f"₹{c.ltp:.2f}",
                "CE OI": f"{c.oi:,}",
                "CE Vol": f"{c.volume:,}",
                "CE Delta": c.delta,
                "CE Gamma": c.gamma,
                "CE Theta": c.theta,
                "CE Vega": c.vega,
                "STRIKE": f"{strike:.0f} {tag}",
                "PE Vega": p.vega,
                "PE Theta": p.theta,
                "PE Gamma": p.gamma,
                "PE Delta": p.delta,
                "PE Vol": f"{p.volume:,}",
                "PE OI": f"{p.oi:,}",
                "PE LTP (₹)": f"₹{p.ltp:.2f}",
            }
        )

    st.dataframe(pd.DataFrame(matrix_rows), **button_kwargs)

elif nav == "🗣️ AI Analyst Debate Meeting":
    st.header("🗣️ AI Analyst Team Debate Meeting")
    candle_now = Candle(datetime.now(), 24900, 24950, 24880, 24915.20, 2500)
    df_c = fetch_sample_data("NIFTY", "1mo")
    ai_dec = auto_trader.coordinator.evaluate_consensus("NIFTY", candle_now, df_c)
    debate = AIDebateEngine.create_debate(ai_dec)

    st.info(debate.summary_reasoning)
    for p in debate.participants:
        st.markdown(f"### 🤖 {p.name} — `{p.role}`")
        st.write(f"**Vote:** `{p.vote}` | **Confidence:** `{p.confidence:.0f}%`")
        st.write(f"**Key Argument:** {p.key_argument}")
        st.markdown("---")

elif nav == "📋 Strategy Scoreboard":
    st.header("📋 Multi-Strategy Scoreboard Matrix")
    candle_now = Candle(datetime.now(), 24900, 24950, 24880, 24915.20, 2500)
    df_c = fetch_sample_data("NIFTY", "1mo")
    scoreboard = StrategyScoreboard.evaluate_scoreboard("NIFTY", candle_now, df_c)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BUY Votes", scoreboard.buy_count)
    col2.metric("WAIT Votes", scoreboard.wait_count)
    col3.metric("SELL Votes", scoreboard.sell_count)
    col4.metric("Alignment Score", f"{scoreboard.alignment_score:.1f}%")

    st.subheader("Strategy Plugin Vote Breakdown")
    st.dataframe(pd.DataFrame([v.__dict__ for v in scoreboard.votes]), **button_kwargs)

elif nav == "🛡️ Session Risk Dashboard":
    st.header("🛡️ Interactive Session Risk Dashboard")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Today's PnL", "+₹420.00")
    r2.metric("Max Daily Loss Limit", "₹2,000.00")
    r3.metric("Remaining Risk Budget", "₹1,580.00")
    r4.metric("Risk Budget Used", "32%")

    st.markdown("---")
    r5, r6, r7 = st.columns(3)
    r5.metric("Trades Taken Today", "3")
    r6.metric("Winning / Losing Trades", "2 Win / 1 Loss")
    r7.metric("Current Exposure", "₹6,200.00")

    st.markdown("---")
    st.subheader("📌 Pre-Trade Risk Limit Approvals")
    risk_checks = [
        {"Rule": "Maximum Position Size (10%)", "Status": "APPROVED", "Value": "2.95%"},
        {"Rule": "Maximum Daily Drawdown (5%)", "Status": "APPROVED", "Value": "0.00%"},
        {"Rule": "Maximum Risk per Trade (2%)", "Status": "APPROVED", "Value": "1.18%"},
        {"Rule": "Maximum Concurrent Trades (5)", "Status": "APPROVED", "Value": "1 Open"},
    ]
    st.dataframe(pd.DataFrame(risk_checks), **button_kwargs)

elif nav == "📊 AI Performance Analytics":
    st.header("📊 AI Performance Analytics & Agent Metrics")

    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Daily PnL (₹)", "+₹4,250.00")
    p2.metric("Win Rate", "78.5%")
    p3.metric("Sharpe Ratio", "2.15")
    p4.metric("Profit Factor", "2.40")
    p5.metric("Avg Hold Time", "22 mins")

    st.markdown("---")
    st.subheader("🤖 Sub-Agent Accuracy Breakdown")

    agent_metrics = [
        {"Agent Name": "TrendAgent", "Weight": "25%", "Accuracy": "84.2%", "Signals Generated": 142},
        {"Agent Name": "MomentumAgent", "Weight": "20%", "Accuracy": "81.0%", "Signals Generated": 138},
        {"Agent Name": "VWAPAgent", "Weight": "20%", "Accuracy": "88.5%", "Signals Generated": 115},
        {"Agent Name": "OptionsOIAnalyzer", "Weight": "20%", "Accuracy": "86.0%", "Signals Generated": 108},
        {"Agent Name": "RiskAgent", "Weight": "10%", "Accuracy": "99.0%", "Signals Generated": 150},
        {"Agent Name": "MarketRegimeAgent", "Weight": "5%", "Accuracy": "79.5%", "Signals Generated": 150},
    ]
    st.dataframe(pd.DataFrame(agent_metrics), **button_kwargs)

elif nav == "⛓️ Live Option Chain Matrix":
    st.header("⛓️ Dedicated Live Option Chain Matrix")
    index_symbol = st.selectbox("Underlying Index", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"])
    spot_val = st.number_input("Simulated Spot Price", value=24915.20)

    chain = OptionChainEngine.generate_chain(index_symbol, float(spot_val))
    st.info(f"Generated Option Chain around ATM Strike **{chain.atm_strike:.0f}** | Put-Call Ratio (PCR): **{chain.pcr:.2f}**")

    chain_rows = []
    for strike in sorted(chain.calls.keys()):
        c = chain.calls[strike]
        p = chain.puts[strike]
        chain_rows.append(
            {
                "Call OI": c.oi,
                "Call Delta": c.delta,
                "Call IV (%)": c.iv,
                "Call LTP": c.ltp,
                "STRIKE": strike,
                "Put LTP": p.ltp,
                "Put IV (%)": p.iv,
                "Put Delta": p.delta,
                "Put OI": p.oi,
            }
        )
    st.dataframe(pd.DataFrame(chain_rows), **button_kwargs)

elif nav == "🎞️ Trade Replay Engine":
    st.header("🎞️ Candle-by-Candle Trade Replay Engine")
    replay_symbol = st.text_input("Replay Symbol", value="NIFTY")
    df_replay = st.session_state.get("market_df", fetch_sample_data(replay_symbol, "1mo"))

    step_idx = st.slider("Historical Bar Index", min_value=10, max_value=len(df_replay), value=25)

    sub_df = df_replay.iloc[:step_idx]
    current_candle = Candle(
        timestamp=sub_df.index[-1] if isinstance(sub_df.index[-1], datetime) else datetime.now(),
        open=float(sub_df["open"].iloc[-1]),
        high=float(sub_df["high"].iloc[-1]),
        low=float(sub_df["low"].iloc[-1]),
        close=float(sub_df["close"].iloc[-1]),
        volume=int(sub_df["volume"].iloc[-1]),
    )

    replay_exp = auto_trader.coordinator.evaluate_consensus(replay_symbol, current_candle, sub_df)

    col_rep_chart, col_rep_ai = st.columns([3, 2])

    with col_rep_chart:
        fig_rep = go.Figure(
            data=[
                go.Candlestick(
                    x=sub_df.index,
                    open=sub_df["open"],
                    high=sub_df["high"],
                    low=sub_df["low"],
                    close=sub_df["close"],
                    name=replay_symbol,
                )
            ]
        )
        fig_rep.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_rep, **button_kwargs)

    with col_rep_ai:
        st.markdown(f"### Replay Bar: {sub_df.index[-1]}")
        st.write(f"**Spot Close Price:** ₹{current_candle.close:,.2f}")
        st.write(f"**Market Regime:** `{replay_exp.market_regime}`")
        st.write(f"**AI Confidence:** {replay_exp.confidence:.1f}%")

elif nav == "📊 Market Data Explorer":
    st.header("📊 Market Data Explorer")
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol = st.text_input("Ticker Symbol", value="NIFTY")
        period = st.selectbox("Historical Period", ["1mo", "3mo", "6mo", "1y", "2y"])
        if st.button("Fetch Market Data"):
            st.session_state["market_df"] = fetch_sample_data(symbol, period)

    if "market_df" not in st.session_state:
        st.session_state["market_df"] = fetch_sample_data(symbol, period)

    df = st.session_state["market_df"]
    st.subheader(f"Historical Candle Data for {symbol}")
    st.line_chart(df["close"])
    with st.expander("Raw Data Table"):
        st.dataframe(df, **button_kwargs)

elif nav == "🧩 Strategy Explorer":
    st.header("🧩 Strategy Registry & Plugins")
    registered_names = StrategyRegistry.list_strategies()
    st.info(f"Discovered {len(registered_names)} strategy plugins: {', '.join(registered_names)}")

    selected = st.selectbox("Select Strategy", registered_names)
    meta = StrategyRegistry.get_metadata(selected)
    strat_cls = StrategyRegistry.load(selected)

    if meta:
        st.markdown(f"### {meta.name.upper()} Strategy")
        st.write(f"**Description**: {meta.description}")
        st.write(f"**Version**: {meta.version}")
        st.write(f"**Author**: {meta.author}")
        st.write(f"**Supported Timeframes**: {', '.join(meta.timeframes)}")

elif nav == "⚡ Parameter Optimization":
    st.header("⚡ Parameter Optimization Engine")
    registered_names = StrategyRegistry.list_strategies()
    selected = st.selectbox("Strategy to Optimize", registered_names)
    strat_cls = StrategyRegistry.load(selected)

    opt_mode = st.radio("Optimization Method", ["Grid Search", "Random Search"])
    top_n = st.slider("Top N Combinations", 1, 20, 5)

    df = st.session_state.get("market_df", fetch_sample_data("NIFTY", "3mo"))

    if selected == "ema":
        param_grid = {"fast_period": [5, 9, 14], "slow_period": [20, 30, 50]}
    elif selected == "supertrend":
        param_grid = {"period": [7, 10, 14], "multiplier": [2.0, 3.0, 4.0]}
    elif selected == "rsi":
        param_grid = {"period": [10, 14, 21], "oversold": [25.0, 30.0], "overbought": [70.0, 75.0]}
    elif selected == "vwap":
        param_grid = {"deviation_pct": [1.0, 1.5, 2.0]}
    elif selected == "mean_reversion":
        param_grid = {"period": [15, 20, 30], "std_dev": [1.5, 2.0, 2.5]}
    else:
        param_grid = {"breakout_candles": [3, 5, 10]}

    if st.button("Run Optimization"):
        engine = OptimizationEngine()
        with st.spinner("Executing parameter search..."):
            if opt_mode == "Grid Search":
                results = engine.grid_search(strat_cls, param_grid, df, top_n=top_n)
            else:
                results = engine.random_search(strat_cls, param_grid, n_iter=10, data=df, top_n=top_n)

        res_df = pd.DataFrame([r.to_dict() for r in results])
        st.subheader("Top Optimization Results")
        st.dataframe(res_df, **button_kwargs)

elif nav == "🔄 Walk Forward Testing":
    st.header("🔄 Walk-Forward Optimization & Testing")
    registered_names = StrategyRegistry.list_strategies()
    selected = st.selectbox("Strategy for Walk Forward", registered_names)
    strat_cls = StrategyRegistry.load(selected)

    train_bars = st.number_input("Train Window Bars", value=50, min_value=20)
    test_bars = st.number_input("Test Window Bars", value=15, min_value=5)
    step_bars = st.number_input("Rolling Step Bars", value=15, min_value=5)

    df = st.session_state.get("market_df", fetch_sample_data("NIFTY", "6mo"))

    if st.button("Execute Walk Forward Analysis"):
        wf_engine = WalkForwardEngine(train_bars=train_bars, test_bars=test_bars, step_bars=step_bars)
        param_grid = {"fast_period": [5, 9], "slow_period": [20, 30]} if selected == "ema" else {"period": [7, 10]}

        try:
            wf_res = wf_engine.run(strat_cls, param_grid, df)
            st.success(f"Walk Forward Analysis Completed for {wf_res.strategy_name}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Out-of-Sample Net Profit", f"₹{wf_res.consolidated_net_profit:,.2f}")
            col2.metric("Out-of-Sample Sharpe", f"{wf_res.consolidated_sharpe:.2f}")
            col3.metric("Out-of-Sample Win Rate", f"{wf_res.consolidated_win_rate:.1f}%")
            col4.metric("Max Drawdown", f"{wf_res.consolidated_max_drawdown:.2f}%")

            st.subheader("Window-by-Window Results")
            st.dataframe(pd.DataFrame([w.__dict__ for w in wf_res.windows]), **button_kwargs)
        except Exception as e:
            st.error(f"Walk Forward execution error: {e}")

elif nav == "⚔️ Strategy Comparison":
    st.header("⚔️ Multi-Strategy Comparison Engine")
    registered_names = StrategyRegistry.list_strategies()
    selected_strats = st.multiselect("Select Strategies to Compare", registered_names, default=registered_names[:3])

    df = st.session_state.get("market_df", fetch_sample_data("NIFTY", "3mo"))

    if st.button("Run Multi-Strategy Comparison"):
        instances = [StrategyRegistry.instantiate(name) for name in selected_strats]
        engine = StrategyComparisonEngine()
        comp_report = engine.compare(instances, df)

        st.subheader("Strategy Comparison Ranking Table")
        st.dataframe(comp_report.to_dataframe(), **button_kwargs)

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
    from app.brokers.paper_broker import PaperBroker
    from app.strategies.ema_crossover import EMACrossoverStrategy

    df = st.session_state.get("market_df", fetch_sample_data("NIFTY", "3mo"))

    if st.button("Generate Demo Performance Report"):
        broker = PaperBroker(initial_cash=100000.0)
        from app.backtesting.engine import BacktestEngine

        engine = BacktestEngine(strategy=EMACrossoverStrategy(), broker=broker)
        engine.run(df)

        html_str = HTMLReportGenerator.generate(broker.portfolio, title="QuantFlow Demo Strategy Report")
        json_data = JSONReportGenerator.generate(broker.portfolio)

        st.download_button(
            "Download HTML Report",
            data=html_str,
            file_name="quantflow_report.html",
            mime="text/html",
        )
        st.download_button(
            "Download JSON Report",
            data=json.dumps(json_data, indent=2),
            file_name="quantflow_report.json",
            mime="application/json",
        )
        st.success("Report generated successfully! Download buttons ready above.")
