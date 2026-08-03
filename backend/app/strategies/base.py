"""Strategy interface for QuantFlow strategy implementations."""

from abc import ABC, abstractmethod
from typing import Optional, Union

import pandas as pd

from app.models.dataclasses import Candle, Signal
from app.models.trading import Order


class Strategy(ABC):
    """Abstract Strategy interface. The strategy never knows which broker it is using."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialise strategy state, indicators, and parameters."""

    def on_tick(self, candle: pd.Series) -> None:
        """Receive a pandas Series candle event for backwards compatibility."""
        pass

    def on_candle(self, candle: Candle) -> Optional[Signal]:
        """Receive the latest candle event and optionally return a Signal."""
        res = self.generate_signal(pd.DataFrame([candle.to_dict()]))
        if isinstance(res, Signal):
            return res
        return None

    @abstractmethod
    def generate_signal(
        self, data: Union[pd.DataFrame, list[Candle]]
    ) -> Union[Optional[Signal], int]:
        """Generate a signal from a window or complete dataset of candles."""

    def on_order(self, order: Order) -> None:
        """Callback received when an order status changes or fills."""
        pass
