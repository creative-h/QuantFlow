"""QuantFlow Professional Quantitative Research & Live Trading Control Panel."""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.paper.live_engine import LivePaperEngine, LivePaperSessionConfig
from app.research.comparison import StrategyComparisonEngine
from app.research.optimization import OptimizationEngine
from app.research.walk_forward import WalkForwardEngine
from app.strategies.registry import StrategyRegistry

st.set_page_config(
    page_title="QuantFlow Research & Trading Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

# Persistent session state for LivePaperEngine in Streamlit
if "live_engine" not in st.session_state:
    st.session_state["live_engine"] = LivePaperEngine()
    st.session_state["live_engine"].recover_session()

live_engine: LivePaperEngine = st.session_state["live_engine"]

st.sidebar.title("⚡ QuantFlow v0.4")
st.sidebar.caption("Quant Research & Live Paper Trading Platform")

nav = st.sidebar.radio(
    "Navigation",
    [
        "⚡ Live Paper Control Panel",
        "📊 Overview & Market Data",
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


if nav == "⚡ Live Paper Control Panel":
    st.header("⚡ Live Paper Trading Control Panel")

    # Engine Status Header
    curr_state = live_engine.state.value
    if curr_state == "RUNNING":
        st.success("● ENGINE STATUS: RUNNING (Real-time Polling & Order Execution Active)")
    elif curr_state == "PAUSED":
        st.warning("⏸️ ENGINE STATUS: PAUSED (Poller Loop Suspended)")
    else:
        st.error("🔴 ENGINE STATUS: STOPPED")

    # Metrics Row
    portfolio = live_engine.broker.portfolio if live_engine.broker else None
    cash = float(portfolio.cash) if portfolio else 100000.0
    equity = float(portfolio.total_equity) if portfolio else cash
    realized = float(portfolio.total_realized_pnl) if portfolio else 0.0
    unrealized = float(portfolio.total_unrealized_pnl) if portfolio else 0.0
    drawdown = portfolio.drawdown_pct if portfolio else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Available Cash", f"${cash:,.2f}")
    col2.metric("Total Equity", f"${equity:,.2f}")
    col3.metric("Realized PnL", f"${realized:,.2f}")
    col4.metric("Unrealized PnL", f"${unrealized:,.2f}")
    col5.metric("Max Drawdown", f"{drawdown:.2f}%")

    st.markdown("---")

    col_ctrl, col_demo = st.columns([2, 2])

    with col_ctrl:
        st.subheader("🎮 Session Controls")
        symbols_input = st.multiselect(
            "Target Symbols",
            ["NIFTY", "RELIANCE", "TCS", "INFY", "AAPL", "MSFT", "TSLA"],
            default=["NIFTY", "AAPL"],
        )
        avail_strats = StrategyRegistry.list_strategies()
        selected_strats = st.multiselect("Active Strategies", avail_strats, default=["ema", "rsi"])
        poll_interval = st.slider("Polling Interval (Seconds)", 1, 60, 5)

        btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
        with btn_c1:
            if st.button("▶️ Start", use_container_width=True):
                cfg = LivePaperSessionConfig(
                    symbols=symbols_input,
                    strategy_names=selected_strats,
                    poll_interval_seconds=poll_interval,
                )
                live_engine.start(cfg)
                st.rerun()

        with btn_c2:
            if st.button("⏸️ Pause", use_container_width=True):
                live_engine.pause()
                st.rerun()

        with btn_c3:
            if st.button("▶️ Resume", use_container_width=True):
                live_engine.resume()
                st.rerun()

        with btn_c4:
            if st.button("⏹️ Stop", use_container_width=True):
                live_engine.stop_sync()
                st.rerun()

    with col_demo:
        st.subheader("⚡ Demo Mode Order Injector")
        st.info("Inject instant paper orders to validate risk, portfolio, and trade journal execution pipeline.")
        demo_sym = st.text_input("Symbol", value="NIFTY")
        demo_side = st.selectbox("Side", ["BUY", "SELL"])
        demo_qty = st.number_input("Quantity", value=10, min_value=1)
        demo_price = st.number_input("Simulated Price ($)", value=100.0, min_value=0.1)

        if st.button("⚡ Inject Demo Order", type="primary", use_container_width=True):
            order = live_engine.inject_demo_order_sync(
                symbol=demo_sym, side_str=demo_side, quantity=int(demo_qty), price=float(demo_price)
            )
            st.success(f"Injected {demo_side} order for {demo_qty} {demo_sym} @ ${demo_price}. Status: {order.status.value}")
            st.rerun()

    st.markdown("---")

    # Positions and Orders Tabbed Table
    t_pos, t_orders, t_alerts = st.tabs(["📊 Open Positions", "📜 Order History", "🔔 Alert Log"])

    with t_pos:
        if live_engine.broker:
            pos_list = list(live_engine.broker.portfolio.positions.values())
            if pos_list:
                df_pos = pd.DataFrame(
                    [
                        {
                            "Symbol": p.symbol,
                            "Quantity": p.quantity,
                            "Average Price": f"${float(p.average_price):,.2f}",
                            "Last Price": f"${float(p.last_price):,.2f}",
                            "Market Value": f"${p.market_value:,.2f}",
                            "Unrealized PnL": f"${p.unrealized_pnl:,.2f}",
                        }
                        for p in pos_list
                    ]
                )
                st.dataframe(df_pos, use_container_width=True)
            else:
                st.info("No open paper positions currently.")
        else:
            st.info("Engine not initialized.")

    with t_orders:
        if live_engine.broker:
            orders_list = list(live_engine.broker._orders.values())
            if orders_list:
                df_ord = pd.DataFrame(
                    [
                        {
                            "ID": o.id,
                            "Symbol": o.request.symbol,
                            "Side": o.request.side.value,
                            "Quantity": o.request.quantity,
                            "Type": o.request.order_type.value,
                            "Status": o.status.value,
                            "Avg Price": f"${float(o.average_price):,.2f}" if o.average_price else "-",
                            "Created At": o.created_at.strftime("%H:%M:%S") if o.created_at else "-",
                        }
                        for o in reversed(orders_list)
                    ]
                )
                st.dataframe(df_ord, use_container_width=True)
            else:
                st.info("No paper orders submitted yet.")
        else:
            st.info("Engine not initialized.")

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
            st.info("No alerts logged in current session.")


elif nav == "📊 Overview & Market Data":
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
