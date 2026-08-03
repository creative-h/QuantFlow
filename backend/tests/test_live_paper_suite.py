"""Release v0.4 comprehensive unit and API test suite."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_live_paper_engine
from app.api.routers.paper import StartPaperSessionRequest
from app.main import app
from app.paper.live_engine import (
    LivePaperEngine,
    LivePaperEngineState,
    LivePaperSessionConfig,
)
from app.services.alert_engine import AlertChannel, AlertEngine, AlertLevel, AlertMessage


def test_live_paper_engine_initial_state():
    engine = LivePaperEngine()
    assert engine.state == LivePaperEngineState.STOPPED
    assert engine.broker is None
    assert engine.config is None


def test_live_paper_engine_state_enum_values():
    assert LivePaperEngineState.STOPPED.value == "STOPPED"
    assert LivePaperEngineState.RUNNING.value == "RUNNING"
    assert LivePaperEngineState.PAUSED.value == "PAUSED"


def test_live_paper_engine_singleton_consistency():
    engine1 = get_live_paper_engine()
    engine2 = get_live_paper_engine()
    assert engine1 is engine2


def test_live_session_config_defaults():
    cfg = LivePaperSessionConfig(symbols=["NIFTY"], strategy_names=["ema"])
    assert cfg.symbols == ["NIFTY"]
    assert cfg.poll_interval_seconds == 5
    assert cfg.initial_cash == 100000.0
    assert cfg.auto_eod_report is True


def test_live_session_config_polling_interval():
    cfg = LivePaperSessionConfig(symbols=["RELIANCE"], strategy_names=["vwap"], poll_interval_seconds=15)
    assert cfg.poll_interval_seconds == 15


def test_live_session_config_auto_eod_override():
    cfg = LivePaperSessionConfig(symbols=["TCS"], strategy_names=["rsi"], auto_eod_report=False)
    assert cfg.auto_eod_report is False


def test_alert_level_and_channel_enums():
    assert AlertLevel.INFO.value == "INFO"
    assert AlertLevel.WARNING.value == "WARNING"
    assert AlertLevel.CRITICAL.value == "CRITICAL"

    assert AlertChannel.CONSOLE.value == "CONSOLE"
    assert AlertChannel.WEBHOOK.value == "WEBHOOK"
    assert AlertChannel.TELEGRAM.value == "TELEGRAM"


def test_alert_message_defaults():
    msg = AlertMessage(title="Info Alert", message="System running smoothly")
    assert msg.extra is None
    assert msg.level == AlertLevel.INFO
    assert msg.channel == AlertChannel.CONSOLE


def test_alert_engine_send_and_history():
    engine = AlertEngine()
    msg = engine.send_alert(
        title="Position Warning",
        message="Position size limit reached for SBIN",
        level=AlertLevel.WARNING,
        extra={"symbol": "SBIN", "qty": 1000},
    )
    assert msg.title == "Position Warning"
    assert msg.extra["qty"] == 1000
    assert len(engine.alert_history) == 1


def test_alert_engine_critical_level():
    engine = AlertEngine()
    msg = engine.send_alert(
        title="Emergency Stop",
        message="Account drawdown threshold breached",
        level=AlertLevel.CRITICAL,
    )
    assert msg.level == AlertLevel.CRITICAL


def test_start_paper_session_request_schema():
    req = StartPaperSessionRequest()
    assert "AAPL" in req.symbols
    assert "ema" in req.strategy_names
    assert req.initial_cash == 100000.0


@pytest.mark.asyncio
async def test_live_paper_engine_pause_resume_edge_cases():
    engine = LivePaperEngine()
    engine.pause()
    assert engine.state == LivePaperEngineState.STOPPED

    engine.resume()
    assert engine.state == LivePaperEngineState.STOPPED


@pytest.mark.asyncio
async def test_live_paper_engine_stop_when_stopped():
    engine = LivePaperEngine()
    res = await engine.stop()
    assert res == {}
    assert engine.state == LivePaperEngineState.STOPPED


@pytest.mark.asyncio
async def test_live_paper_engine_empty_symbols_process_tick():
    engine = LivePaperEngine()
    config = LivePaperSessionConfig(symbols=[], strategy_names=["ema"])
    engine.start(config)
    placed = await engine.process_tick()
    assert placed == []
    await engine.stop()


def test_paper_router_full_control_flow():
    client = TestClient(app)
    status_res = client.get("/paper/status")
    assert status_res.status_code == 200
    assert "active_strategies" in status_res.json()

    start_payload = {
        "symbols": ["MSFT"],
        "strategy_names": ["rsi"],
        "poll_interval_seconds": 5,
        "initial_cash": 75000.0,
        "auto_eod_report": False,
    }
    res_start = client.post("/paper/start", json=start_payload)
    assert res_start.status_code == 200

    res_pause = client.post("/paper/pause")
    assert res_pause.status_code == 200

    res_resume = client.post("/paper/resume")
    assert res_resume.status_code == 200

    res_stop = client.post("/paper/stop")
    assert res_stop.status_code == 200
