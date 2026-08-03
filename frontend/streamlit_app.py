"""QuantFlow Professional Quantitative Research Platform Dashboard."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.marketdata.csv_provider import CSVProvider
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.research.comparison import StrategyComparisonEngine
from app.research.optimization import OptimizationEngine
from app.research.walk_forward import WalkForwardEngine
from app.strategies.registry import StrategyRegistry

st.set_page_config(
    page_title="QuantFlow Research Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Discover strategy plugins automatically
StrategyRegistry.discover_strategies()

st.sidebar.title("⚡ QuantFlow v0.3")
st.sidebar.caption("Quant Research & Strategy Optimization Platform")

nav = st.sidebar.radio(
    "Navigation",
    [
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


if nav == "📊 Overview & Market Data":
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
