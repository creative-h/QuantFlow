"""Market State Engine detecting Indian trading sessions (PREOPEN, OPEN, POST MARKET, CLOSED), weekends, and holidays."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional


@dataclass
class MarketStatusInfo:
    """Dataclass storing current Indian market session telemetry."""

    timestamp: datetime
    status: str  # "PREOPEN", "OPEN", "POST MARKET", "CLOSED"
    is_trading_day: bool
    is_weekend: bool
    is_holiday: bool
    holiday_name: Optional[str] = None
    next_session_time: Optional[datetime] = None


class MarketStateEngine:
    """Engine monitoring Indian Index Market session status and calendar."""

    NSE_HOLIDAYS_2026 = {
        "2026-01-26": "Republic Day",
        "2026-03-08": "Mahashivratri",
        "2026-03-25": "Holi",
        "2026-03-29": "Good Friday",
        "2026-04-14": "Dr. Ambedkar Jayanti",
        "2026-04-21": "Ram Navami",
        "2026-05-01": "Maharashtra Day",
        "2026-08-15": "Independence Day",
        "2026-10-02": "Mahatma Gandhi Jayanti",
        "2026-10-24": "Dussehra",
        "2026-11-01": "Diwali Laxmi Pujan",
        "2026-12-25": "Christmas",
    }

    @classmethod
    def get_market_state(cls, now_dt: Optional[datetime] = None) -> MarketStatusInfo:
        """Evaluate current Indian market operational state."""
        now = now_dt or datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        current_time = now.time()

        is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
        is_holiday = date_str in cls.NSE_HOLIDAYS_2026
        holiday_name = cls.NSE_HOLIDAYS_2026.get(date_str) if is_holiday else None

        is_trading_day = not is_weekend and not is_holiday

        preopen_start = time(9, 0, 0)
        open_start = time(9, 15, 0)
        open_end = time(15, 30, 0)
        post_end = time(16, 0, 0)

        if not is_trading_day:
            status = "CLOSED"
        else:
            if preopen_start <= current_time < open_start:
                status = "PREOPEN"
            elif open_start <= current_time < open_end:
                status = "OPEN"
            elif open_end <= current_time < post_end:
                status = "POST MARKET"
            else:
                status = "CLOSED"

        return MarketStatusInfo(
            timestamp=now,
            status=status,
            is_trading_day=is_trading_day,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            holiday_name=holiday_name,
        )

    @classmethod
    def is_market_open(cls, now_dt: Optional[datetime] = None) -> bool:
        """Return True if market is currently in OPEN session."""
        state = cls.get_market_state(now_dt)
        return state.status == "OPEN"
