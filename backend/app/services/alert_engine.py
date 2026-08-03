"""Multi-channel notification and alert engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


class AlertLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertChannel(str, Enum):
    CONSOLE = "CONSOLE"
    WEBHOOK = "WEBHOOK"
    TELEGRAM = "TELEGRAM"


@dataclass
class AlertMessage:
    """Dataclass holding an alert payload."""

    title: str
    message: str
    level: AlertLevel = AlertLevel.INFO
    channel: AlertChannel = AlertChannel.CONSOLE
    extra: Optional[Dict[str, Any]] = None


class AlertEngine:
    """Multi-channel alert dispatcher for trading signals, fills, and risk events."""

    def __init__(self, enabled_channels: Optional[List[AlertChannel]] = None) -> None:
        self.enabled_channels = enabled_channels or [AlertChannel.CONSOLE]
        self.alert_history: List[AlertMessage] = []

    def send_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        channel: AlertChannel = AlertChannel.CONSOLE,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AlertMessage:
        """Send an alert message across configured channels."""
        alert = AlertMessage(title=title, message=message, level=level, channel=channel, extra=extra)
        self.alert_history.append(alert)

        # 1. Console / Loguru logging
        log_msg = f"[ALERT - {level.value}] {title}: {message}"
        if level == AlertLevel.CRITICAL:
            logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # 2. Webhook / Telegram placeholders
        if channel == AlertChannel.WEBHOOK:
            self._dispatch_webhook(alert)
        elif channel == AlertChannel.TELEGRAM:
            self._dispatch_telegram(alert)

        return alert

    def _dispatch_webhook(self, alert: AlertMessage) -> None:
        logger.debug("Dispatched webhook alert: {}", alert.title)

    def _dispatch_telegram(self, alert: AlertMessage) -> None:
        logger.debug("Dispatched Telegram alert: {}", alert.title)
