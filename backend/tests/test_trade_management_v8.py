"""Unit tests for QuantFlow v8.0 Trade Management Engine."""

from datetime import datetime, timedelta
import pytest

from app.trade_management.entry_engine import EntryEngine, EntryTranche
from app.trade_management.exit_engine import ExitEngine, ExitTranche
from app.trade_management.position_sizer import ProfessionalPositionSizer
from app.trade_management.target_manager import TargetManager, TargetStatus
from app.trade_management.trailing_stop_engine import TrailingStopEngine


def test_position_sizer_risk_based():
    res = ProfessionalPositionSizer.calculate_risk_based_size(
        portfolio_value=100000.0,
        risk_pct=2.0,
        entry_price=118.0,
        stop_loss=105.0,
        lot_size=25,
    )
    assert res["lots"] >= 1
    assert res["quantity"] >= 25
    assert res["risk_amount"] == 2000.0


def test_position_sizer_kelly_fraction():
    kelly = ProfessionalPositionSizer.calculate_kelly_fraction(win_rate=65.0, reward_risk_ratio=2.5)
    assert 0.01 <= kelly <= 0.25
    assert round(kelly, 2) == 0.26 or round(kelly, 2) == 0.25 or round(kelly, 2) == 0.21


def test_entry_engine_tranches():
    ee = EntryEngine(target_quantity=100, num_tranches=2)
    t1 = ee.execute_initial_entry(price=100.0, quantity=50)
    assert isinstance(t1, EntryTranche)
    assert ee.get_total_quantity() == 50

    t2 = ee.execute_scale_in(price=110.0, quantity=50)
    assert ee.get_total_quantity() == 100
    assert ee.get_average_entry_price() == 105.0


def test_exit_engine_tranches():
    ee = ExitEngine()
    t1 = ee.execute_partial_exit(price=120.0, quantity=50, reason="TARGET_1")
    assert isinstance(t1, ExitTranche)
    assert ee.get_total_exited_quantity() == 50
    assert ee.get_realized_pnl(avg_entry_price=100.0) == 1000.0


def test_target_manager_multi_target_and_move_sl_cost():
    tm = TargetManager(entry_price=100.0, stop_loss=90.0, t1=115.0, t2=130.0, t3=150.0)
    assert tm.current_stop_loss == 90.0

    # Price hits T1
    triggered = tm.check_targets(current_price=118.0)
    assert len(triggered) == 1
    assert triggered[0]["target_id"] == 1
    assert tm.current_stop_loss == 100.0  # SL moved to cost!


def test_trailing_stop_engine_atr_and_time_stop():
    now = datetime.now() - timedelta(minutes=50)
    tse = TrailingStopEngine(entry_price=100.0, initial_stop_loss=90.0, entry_time=now, max_holding_time_mins=45)

    assert tse.is_time_stop_breached()

    # Update trailing stop
    new_sl = tse.update_trailing_stop(current_price=120.0, atr=5.0)
    assert new_sl == 110.0  # 120 - 2.0*5 = 110
    assert not tse.is_stop_loss_breached(current_price=115.0)
    assert tse.is_stop_loss_breached(current_price=108.0)
