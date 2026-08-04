"""QuantFlow Professional AI Trading Terminal & Research Platform."""

import json
import sys
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.analytics.ai_reasoner import AIExplanation, AIReasoner, MarketRegime
from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.indicators.engine import IndicatorEngine
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.paper.live_engine import LivePaperEngine, LivePaperSessionConfig
from app.research.comparison import StrategyComparisonEngine
from app.research.optimization import OptimizationEngine
from app.research.walk_forward import WalkForwardEngine
from app.strategies.registry import StrategyRegistry

st.set_page_config(
    page_title="QuantFlow AI Trading Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for LivePaperEngine in Streamlit
if "live_engine" not in st.session_state:
    st.session_state["live_engine"] = LivePaperEngine()
    st.session_state["live_engine"].recover_session()

live_engine: LivePaperEngine = st.session_state["live_engine"]

# Custom Dark Theme CSS styling for AI Terminal
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    .ticker-bar {
        background-color: #161b22;
        padding: 8px 16px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 14px;
        margin-bottom: 12px;
        border: 1px solid #30363d;
    }
    .ai-card {
        background-color: #161b22;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 12px;
    }
    .regime-pill {
        background-color: #238636;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Top Live Ticker Strip
st.markdown(
    """
    <div class="ticker-bar">
        <b>● MARKET FEED</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>NIFTY 50:</b> 24,915.20 <span style="color:#3fb950">▲ +45.10</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>BANKNIFTY:</b> 55,201.00 <span style="color:#3fb950">▲ +120.50</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>INDIA VIX:</b> 12.80 &nbsp;&nbsp;&nbsp;&nbsp;
        <b>AAPL:</b> $224.50 <span style="color:#3fb950">▲ +1.20</span> &nbsp;&nbsp;&nbsp;&nbsp;
        <b>MSFT:</b> $448.10 <span style="color:#f85149">▼ -2.40</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("⚡ QuantFlow Terminal")
st.sidebar.caption("v0.5 - AI Trading & Research Platform")

nav = st.sidebar.radio(
    "Workstation Views",
    [
        "🖥️ AI Trading Terminal",
        "🎞️ Trade Replay Engine",
        "📊 Market Data Explorer",
        "🧩 Strategy Explorer",
        "⚡ Parameter Optimization",
        "🔄 Walk Forward Testing",
        "⚔️ Strategy Comparison",
        "📄 Reports & Analytics",
    ],
)


# Helper function to get market data
def fetch_sample_data(symbol: str = "AAPL", period: str = "1mo") -> pd.DataFrame:
    try:
        provider = YahooFinanceProvider()
        return provider.get_candles(symbol, period=period)
    except Exception:
        # Fallback synthetic generator
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        import numpy as np

        np.random.seed(42)
        price = 100.0 + np.cumsum(np.random.randn(100))
        return pd.DataFrame(
            {
                "open": price - 0.5,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "volume": 10000,
            },
            index=dates,
        )


if nav == "🖥️ AI Trading Terminal":
    # Terminal Header & Controls Row
    curr_state = live_engine.state.value
    st_col1, st_col2 = st.columns([3, 1])

    with st_col1:
        if curr_state == "RUNNING":
            st.markdown("### 🟢 QuantFlow AI Terminal — **LIVE TRADING RUNNING**")
        elif curr_state == "PAUSED":
            st.markdown("### ⏸️ QuantFlow AI Terminal — **SESSION PAUSED**")
        else:
            st.markdown("### 🔴 QuantFlow AI Terminal — **SESSION STOPPED**")

    # Metrics Strip
    portfolio = live_engine.broker.portfolio if live_engine.broker else None
    cash = float(portfolio.cash) if portfolio else 100000.0
    equity = float(portfolio.total_equity) if portfolio else cash
    realized = float(portfolio.total_realized_pnl) if portfolio else 0.0
    unrealized = float(portfolio.total_unrealized_pnl) if portfolio else 0.0
    drawdown = portfolio.drawdown_pct if portfolio else 0.0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Available Cash", f"${cash:,.2f}")
    m2.metric("Total Equity", f"${equity:,.2f}")
    m3.metric("Realized PnL", f"${realized:,.2f}")
    m4.metric("Unrealized PnL", f"${unrealized:,.2f}")
    m5.metric("Max Drawdown", f"{drawdown:.2f}%")

    st.markdown("---")

    # Main Grid: Left Chart & Controls (3 cols), Right AI Reasoning (2 cols)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        target_symbol = st.selectbox("Symbol View", ["AAPL", "MSFT", "NIFTY", "RELIANCE", "TCS"], index=0)
        df_chart = st.session_state.get("market_df", fetch_sample_data(target_symbol, "1mo"))

        # Compute indicators for overlays
        df_chart["ema20"] = IndicatorEngine.ema(df_chart, 20)
        df_chart["ema50"] = IndicatorEngine.ema(df_chart, 50)
        df_chart["vwap"] = IndicatorEngine.vwap(df_chart)

        # Plotly Candlestick Chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])

        # Candlestick trace
        fig.add_trace(
            go.Candlestick(
                x=df_chart.index,
                open=df_chart["open"],
                high=df_chart["high"],
                low=df_chart["low"],
                close=df_chart["close"],
                name="OHLC",
            ),
            row=1,
            col=1,
        )

        # Indicator overlays
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

        # Plot Buy/Sell Order execution markers on chart if orders exist
        if live_engine.broker:
            orders_list = live_engine.broker.list_orders()
            buy_x, buy_y, sell_x, sell_y = [], [], [], []
            for o in orders_list:
                if o.request.symbol.upper() == target_symbol.upper() and o.average_price:
                    ts = o.created_at if isinstance(o.created_at, datetime) else df_chart.index[-1]
                    if o.request.side.value == "BUY":
                        buy_x.append(ts)
                        buy_y.append(float(o.average_price))
                    else:
                        sell_x.append(ts)
                        sell_y.append(float(o.average_price))

            if buy_x:
                fig.add_trace(
                    go.Scatter(
                        x=buy_x,
                        y=buy_y,
                        mode="markers",
                        marker=dict(symbol="triangle-up", size=14, color="#3fb950"),
                        name="BUY Marker",
                    ),
                    row=1,
                    col=1,
                )
            if sell_x:
                fig.add_trace(
                    go.Scatter(
                        x=sell_x,
                        y=sell_y,
                        mode="markers",
                        marker=dict(symbol="triangle-down", size=14, color="#f85149"),
                        name="SELL Marker",
                    ),
                    row=1,
                    col=1,
                )

        # Volume Subplot
        fig.add_trace(
            go.Bar(x=df_chart.index, y=df_chart["volume"], marker_color="#30363d", name="Volume"),
            row=2,
            col=1,
        )

        fig.update_layout(
            template="plotly_dark",
            height=500,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False,
            paper_bgcolor="#0b0e14",
            plot_bgcolor="#0b0e14",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Session Controls Bar
        st.subheader("🎮 Live Trading Controls")
        ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4, ctrl_c5 = st.columns([1, 1, 1, 1, 1.5])

        with ctrl_c1:
            if st.button("▶️ Start Session", use_container_width=True):
                cfg = LivePaperSessionConfig(symbols=[target_symbol], strategy_names=["ema"])
                live_engine.start(cfg)
                st.rerun()

        with ctrl_c2:
            if st.button("⏸️ Pause", use_container_width=True):
                live_engine.pause()
                st.rerun()

        with ctrl_c3:
            if st.button("▶️ Resume", use_container_width=True):
                live_engine.resume()
                st.rerun()

        with ctrl_c4:
            if st.button("⏹️ Stop", use_container_width=True):
                live_engine.stop_sync()
                st.rerun()

        with ctrl_c5:
            if st.button("⚡ Inject Demo Signal", type="primary", use_container_width=True):
                order = live_engine.inject_demo_order_sync(
                    symbol=target_symbol, side_str="BUY", quantity=10, price=float(df_chart["close"].iloc[-1])
                )
                st.success(f"Injected demo BUY order for {target_symbol}. Status: {order.status.value}")
                st.rerun()

    with col_right:
        st.subheader("🤖 AI Reasoning & Market Commentary")

        # Fetch latest AI Explanation for target symbol
        ai_exp: AIExplanation = live_engine.recent_ai_explanations.get(
            target_symbol.upper(),
            AIReasoner.evaluate(
                symbol=target_symbol,
                candle=Candle(
                    timestamp=datetime.now(),
                    open=float(df_chart["open"].iloc[-1]),
                    high=float(df_chart["high"].iloc[-1]),
                    low=float(df_chart["low"].iloc[-1]),
                    close=float(df_chart["close"].iloc[-1]),
                    volume=int(df_chart["volume"].iloc[-1]),
                ),
                history=df_chart,
            ),
        )

        st.markdown(
            f"""
            <div class="ai-card">
                <h4>AI Decision: <b>{ai_exp.decision}</b></h4>
                <p><b>Market Regime:</b> <span class="regime-pill">{ai_exp.market_regime.value}</span></p>
                <p><b>AI Confidence Score:</b> {ai_exp.confidence_score:.1f}%</p>
                <hr style="border-color:#30363d;"/>
                <p><b>Plain Language Breakdown:</b></p>
                <p><i>"{ai_exp.explanation}"</i></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("✓ Technical Alignment Checklist")
        for rule_name, passed in ai_exp.checklist.items():
            if passed:
                st.markdown(f"🟢 **{rule_name}**: Confirmed & Approved")
            else:
                st.markdown(f"🔴 **{rule_name}**: Pending / Not Met")

        st.markdown("---")
        st.subheader("💼 Active Positions HUD")
        if live_engine.broker:
            pos_list = list(live_engine.broker.portfolio.positions.values())
            if pos_list:
                for p in pos_list:
                    if p.quantity != 0:
                        st.info(
                            f"**{p.symbol}** | Qty: {p.quantity} | Avg: ${float(p.average_price):,.2f} | Last: ${float(p.last_price):,.2f} | PnL: **${p.unrealized_pnl:,.2f}**"
                        )
            else:
                st.write("No active open positions.")
        else:
            st.write("Engine uninitialized.")

    st.markdown("---")

    # Order Audit Log
    t_orders, t_alerts = st.tabs(["📜 Order Execution Audit Log", "🔔 System Alert Stream"])

    with t_orders:
        if live_engine.broker:
            orders_list = live_engine.broker.list_orders()
            if orders_list:
                df_ord = pd.DataFrame(
                    [
                        {
                            "Order ID": o.id,
                            "Symbol": o.request.symbol,
                            "Side": o.request.side.value,
                            "Quantity": o.request.quantity,
                            "Type": o.request.order_type.value,
                            "Status": o.status.value,
                            "Avg Price": f"${float(o.average_price):,.2f}" if o.average_price else "-",
                            "Timestamp": o.created_at.strftime("%H:%M:%S") if o.created_at else "-",
                        }
                        for o in reversed(orders_list)
                    ]
                )
                st.dataframe(df_ord, use_container_width=True)
            else:
                st.info("No orders executed yet.")

    with t_alerts:
        if live_engine.alert_engine.alert_history:
            df_alt = pd.DataFrame(
                [
                    {
                        "Title": a.title,
                        "Message": a.message,
                        "Level": a.level.value,
                        "Channel": a.channel.value,
                    }
                    for a in reversed(live_engine.alert_engine.alert_history)
                ]
            )
            st.dataframe(df_alt, use_container_width=True)
        else:
            st.info("No alerts logged.")

elif nav == "🎞️ Trade Replay Engine":
    st.header("🎞️ Candle-by-Candle Trade Replay Engine")
    st.info("Replay historical price action candle-by-candle to inspect AI reasoning and trade executions bar-by-bar.")

    replay_symbol = st.text_input("Replay Symbol", value="AAPL")
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

    replay_exp = AIReasoner.evaluate(
        symbol=replay_symbol, candle=current_candle, history=sub_df, strategy_name="EMA Crossover"
    )

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
        st.plotly_chart(fig_rep, use_container_width=True)

    with col_rep_ai:
        st.markdown(f"### Replay Bar: {sub_df.index[-1]}")
        st.write(f"**Close Price:** ${current_candle.close:,.2f}")
        st.write(f"**Market Regime:** `{replay_exp.market_regime.value}`")
        st.write(f"**AI Confidence:** {replay_exp.confidence_score:.1f}%")
        st.info(f"**AI Commentary:** {replay_exp.explanation}")

elif nav == "📊 Market Data Explorer":
    st.header("📊 Market Data Explorer")
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol = st.text_input("Ticker Symbol", value="AAPL")
        period = st.selectbox("Historical Period", ["1mo", "3mo", "6mo", "1y", "2y"])
        if st.button("Fetch Market Data"):
            st.session_state["market_df"] = fetch_sample_data(symbol, period)

    if "market_df" not in st.session_state:
        st.session_state["market_df"] = fetch_sample_data(symbol, period)

    df = st.session_state["market_df"]
    st.subheader(f"Historical Candle Data for {symbol}")
    st.line_chart(df["close"])
    with st.expander("Raw Data Table"):
        st.dataframe(df, use_container_width=True)

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

    df = st.session_state.get("market_df", fetch_sample_data("AAPL", "3mo"))

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
        st.dataframe(res_df, use_container_width=True)

elif nav == "🔄 Walk Forward Testing":
    st.header("🔄 Walk-Forward Optimization & Testing")
    registered_names = StrategyRegistry.list_strategies()
    selected = st.selectbox("Strategy for Walk Forward", registered_names)
    strat_cls = StrategyRegistry.load(selected)

    train_bars = st.number_input("Train Window Bars", value=50, min_value=20)
    test_bars = st.number_input("Test Window Bars", value=15, min_value=5)
    step_bars = st.number_input("Rolling Step Bars", value=15, min_value=5)

    df = st.session_state.get("market_df", fetch_sample_data("AAPL", "6mo"))

    if st.button("Execute Walk Forward Analysis"):
        wf_engine = WalkForwardEngine(train_bars=train_bars, test_bars=test_bars, step_bars=step_bars)
        param_grid = {"fast_period": [5, 9], "slow_period": [20, 30]} if selected == "ema" else {"period": [7, 10]}

        try:
            wf_res = wf_engine.run(strat_cls, param_grid, df)
            st.success(f"Walk Forward Analysis Completed for {wf_res.strategy_name}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Out-of-Sample Net Profit", f"${wf_res.consolidated_net_profit:,.2f}")
            col2.metric("Out-of-Sample Sharpe", f"{wf_res.consolidated_sharpe:.2f}")
            col3.metric("Out-of-Sample Win Rate", f"{wf_res.consolidated_win_rate:.1f}%")
            col4.metric("Max Drawdown", f"{wf_res.consolidated_max_drawdown:.2f}%")

            st.subheader("Window-by-Window Results")
            st.dataframe(pd.DataFrame([w.__dict__ for w in wf_res.windows]), use_container_width=True)
        except Exception as e:
            st.error(f"Walk Forward execution error: {e}")

elif nav == "⚔️ Strategy Comparison":
    st.header("⚔️ Multi-Strategy Comparison Engine")
    registered_names = StrategyRegistry.list_strategies()
    selected_strats = st.multiselect("Select Strategies to Compare", registered_names, default=registered_names[:3])

    df = st.session_state.get("market_df", fetch_sample_data("AAPL", "3mo"))

    if st.button("Run Multi-Strategy Comparison"):
        instances = [StrategyRegistry.instantiate(name) for name in selected_strats]
        engine = StrategyComparisonEngine()
        comp_report = engine.compare(instances, df)

        st.subheader("Strategy Comparison Ranking Table")
        st.dataframe(comp_report.to_dataframe(), use_container_width=True)

elif nav == "📄 Reports & Analytics":
    st.header("📄 Performance Reports & HTML Export")
    from app.brokers.paper_broker import PaperBroker
    from app.strategies.ema_crossover import EMACrossoverStrategy

    df = st.session_state.get("market_df", fetch_sample_data("AAPL", "3mo"))

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
