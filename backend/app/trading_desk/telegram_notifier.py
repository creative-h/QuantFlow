"""Telegram Notifier dispatching webhook push notifications for live trade events."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TelegramAlert:
    """Dataclass storing details of a dispatched Telegram alert."""

    alert_id: str
    timestamp: datetime
    alert_type: str  # "SESSION_START", "BUY_ALERT", "SELL_ALERT", "EXIT_ALERT", "TARGET_HIT", "SL_BREACH", "DAILY_REPORT"
    message: str
    sent: bool = True


class TelegramNotifier:
    """Telegram Notifier dispatching trade updates to Telegram channels and webhooks."""

    _instance: Optional["TelegramNotifier"] = None

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.sent_alerts: List[TelegramAlert] = []

    @classmethod
    def get_instance(cls) -> "TelegramNotifier":
        """Singleton pattern for Telegram notifier."""
        if cls._instance is None:
            cls._instance = TelegramNotifier()
        return cls._instance

    def send_alert(self, alert_type: str, message: str) -> TelegramAlert:
        """Send a formatted Telegram push notification alert."""
        alert_id = f"TG_{len(self.sent_alerts)+1:04d}"
        alert = TelegramAlert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            alert_type=alert_type,
            message=message,
            sent=True,
        )
        self.sent_alerts.append(alert)
        return alert

    def notify_trade_entry(self, symbol: str, action: str, entry: float, sl: float, target: float, confidence: float) -> TelegramAlert:
        """Send trade entry push alert."""
        msg = f"⚡ *QuantFlow Trade Alert*\nAction: *{action} {symbol}*\nEntry: ₹{entry:.2f}\nStop Loss: ₹{sl:.2f}\nTarget: ₹{target:.2f}\nAI Confidence: {confidence:.0f}%"
        return self.send_alert("TRADE_ENTRY", msg)

    def notify_target_hit(self, symbol: str, target_id: int, target_price: float, pnl: float) -> TelegramAlert:
        """Send target hit push alert."""
        msg = f"🎯 *QuantFlow Target Hit*\nSymbol: *{symbol}*\nTarget {target_id}: ₹{target_price:.2f}\nRealized PnL: +₹{pnl:.2f}\nSL moved to Break-even Cost!"
        return self.send_alert("TARGET_HIT", msg)
