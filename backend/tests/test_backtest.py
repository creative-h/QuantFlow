import pandas as pd

from app.backtesting.engine import BacktestEngine
from app.strategies.base import Strategy


class BuyOnceStrategy(Strategy):
    def initialize(self) -> None:
        return None

    def generate_signal(self, data: pd.DataFrame) -> int:
        return 1 if len(data) == 1 else 0


def test_backtest_produces_equity_curve() -> None:
    data = pd.DataFrame({"open": [100, 101, 102], "high": [101, 102, 103], "low": [99, 100, 101], "close": [100, 101, 102], "volume": [1000, 1000, 1000]})
    result = BacktestEngine().run(data, BuyOnceStrategy())
    assert len(result.equity_curve) == len(data)
    assert result.net_profit > 0
