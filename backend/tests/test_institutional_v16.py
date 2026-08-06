"""Unit tests for QuantFlow v16.0 Real Market Paper Trading Engine & Live MTM Workstation."""

from datetime import datetime
import pytest

from app.analytics.live_validation import LiveValidationPanel, TerminalComparisonRow
from app.marketdata.data_quality import DataQualityEngine, DataQualityReport
from app.marketdata.live_greeks_engine import LiveGreeksEngine, LiveGreeksSnapshot
from app.marketdata.live_option_chain import LiveOptionChainMatrix, OptionChainMatrixSnapshot
from app.marketdata.live_option_price_engine import LiveOptionPriceEngine, OptionContractTick
from app.paper.contract_note import ZerodhaContractNote, ZerodhaContractNoteCalculator
from app.paper.real_execution_sim import RealExecutionResult, RealExecutionSimulator
from app.risk.real_margin_engine import MarginBreakdown, RealMarginEngine
from app.trading_desk.mtm_engine import MTMEngine, PortfolioMTMHeader, PositionMTMSnapshot


def test_live_option_price_engine():
    engine = LiveOptionPriceEngine.get_instance()
    ltp = engine.get_live_option_price("28th Jul 24250 CE")
    assert ltp == 218.50


def test_mtm_engine():
    pos_mtm = MTMEngine.calculate_position_mtm("TRD_201", "28th Jul 24250 CE", 260, 218.50, 245.00)
    assert isinstance(pos_mtm, PositionMTMSnapshot)
    assert pos_mtm.unrealized_pnl == 6890.0
    assert pos_mtm.running_status == "RUNNING_PROFIT"

    header = MTMEngine.get_portfolio_mtm_header([pos_mtm])
    assert isinstance(header, PortfolioMTMHeader)
    assert header.total_mtm == 6890.0


def test_live_greeks_engine():
    greeks = LiveGreeksEngine.calculate_greeks(24636.0, 24250.0, 218.50, "CE")
    assert isinstance(greeks, LiveGreeksSnapshot)
    assert greeks.delta == 0.62
    assert greeks.intrinsic_value == 386.0
    assert greeks.probability_itm > 50.0


def test_live_option_chain_matrix():
    matrix = LiveOptionChainMatrix.get_live_chain_matrix("NIFTY", 24636.0)
    assert isinstance(matrix, OptionChainMatrixSnapshot)
    assert len(matrix.rows) >= 5
    assert matrix.pcr == 1.22


def test_real_margin_engine():
    margin = RealMarginEngine.calculate_margin(260, 218.50, is_selling=False)
    assert isinstance(margin, MarginBreakdown)
    assert margin.premium_margin == 56810.0
    assert margin.margin_utilized_pct > 0.0


def test_real_execution_simulator():
    exec_res = RealExecutionSimulator.simulate_order_fill("BUY", 218.50, 260)
    assert isinstance(exec_res, RealExecutionResult)
    assert exec_res.filled_price > 218.50  # Includes bid/ask spread & slippage
    assert exec_res.latency_ms == 45.0


def test_zerodha_contract_note_calculator():
    cn = ZerodhaContractNoteCalculator.calculate_contract_note(218.50, 245.00, 260)
    assert isinstance(cn, ZerodhaContractNote)
    assert cn.flat_brokerage == 40.0
    assert cn.stt > 0.0
    assert cn.net_realized_pnl < cn.gross_pnl  # Net PnL is gross PnL minus charges


def test_live_validation_panel():
    rows = LiveValidationPanel.validate_terminal_prices()
    assert len(rows) >= 2
    assert rows[0].diff_pct < 0.50  # Within ±0.5% threshold
    assert rows[0].status == "MATCHED"


def test_data_quality_engine():
    engine = DataQualityEngine.get_instance()
    assert engine.validate_tick(218.50, 218.00) is True
    assert engine.validate_tick(500.00, 218.00) is False  # Outlier spike rejected

    report = engine.get_quality_report()
    assert isinstance(report, DataQualityReport)
    assert report.heartbeat_status == "HEALTHY"
