"""Candle-replay backtesting engine."""

from dataclasses import dataclass

import pandas as pd

from app.backtesting.statistics import max_drawdown, sharpe_ratio
from app.models.dataclasses import SignalSide
from app.strategies.base import Strategy


@dataclass(frozen=True)
class BacktestResult:
    net_profit: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    trades: pd.DataFrame
    equity_curve: pd.Series


class BacktestEngine:
    """Replay candles and apply target-position signals on next close."""

    def __init__(self, initial_capital: float = 100_000.0, commission_rate: float = 0.0003) -> None:
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate

    def run(self, data: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        """Execute a strategy against canonical OHLCV candle data."""

        required = {"open", "high", "low", "close", "volume"}
        if not required.issubset(data.columns):
            raise ValueError(f"data must contain {sorted(required)}")
        strategy.initialize()
        position, cash = 0, self.initial_capital
        equity_values: list[float] = []
        trades: list[dict[str, object]] = []
        for index in range(len(data)):
            window = data.iloc[: index + 1]
            candle = window.iloc[-1]
            strategy.on_tick(candle)
            signal = strategy.generate_signal(window)

            sig_val = 0
            if hasattr(signal, "side"):
                if signal.side == SignalSide.BUY:
                    sig_val = 1
                elif signal.side == SignalSide.SELL:
                    sig_val = -1
            elif isinstance(signal, (int, float)):
                sig_val = int(signal)

            target = 1 if sig_val > 0 else -1 if sig_val < 0 else position
            if target != position:
                quantity = target - position
                price = float(candle["close"])
                fee = abs(quantity) * price * self.commission_rate
                cash -= quantity * price + fee
                trades.append({"timestamp": window.index[-1], "quantity": quantity, "price": price, "fee": fee})
                position = target
            equity_values.append(cash + position * float(candle["close"]))
        equity = pd.Series(equity_values, index=data.index, name="equity")
        trade_frame = pd.DataFrame(trades)
        returns = equity.pct_change().dropna()
        pnl = trade_frame.get("quantity", pd.Series(dtype=float)) * trade_frame.get("price", pd.Series(dtype=float)) * -1
        gains = pnl[pnl > 0].sum()
        losses = -pnl[pnl < 0].sum()
        return BacktestResult(
            net_profit=float(equity.iloc[-1] - self.initial_capital),
            max_drawdown=max_drawdown(equity),
            win_rate=float((pnl > 0).mean()) if not pnl.empty else 0.0,
            profit_factor=float(gains / losses) if losses else float("inf") if gains else 0.0,
            sharpe_ratio=sharpe_ratio(returns),
            trades=trade_frame,
            equity_curve=equity,
        )
