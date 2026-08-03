"""Unit tests for AlertEngine."""

from app.services.alert_engine import AlertChannel, AlertEngine, AlertLevel


def test_send_alert_console():
    engine = AlertEngine()
    alert = engine.send_alert(
        title="Test Signal",
        message="BUY RELIANCE @ 2500",
        level=AlertLevel.INFO,
        channel=AlertChannel.CONSOLE,
    )
    assert alert.title == "Test Signal"
    assert len(engine.alert_history) == 1


def test_send_alert_multi_channel():
    engine = AlertEngine(enabled_channels=[AlertChannel.CONSOLE, AlertChannel.TELEGRAM])
    alert = engine.send_alert(
        title="Drawdown Breach",
        message="Max drawdown exceeded 15%",
        level=AlertLevel.CRITICAL,
        channel=AlertChannel.TELEGRAM,
        extra={"drawdown_pct": 16.5},
    )
    assert alert.level == AlertLevel.CRITICAL
    assert alert.extra["drawdown_pct"] == 16.5
