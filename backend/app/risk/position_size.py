"""Risk-based position-sizing calculation."""

from decimal import Decimal


def position_size(capital: Decimal, risk_fraction: Decimal, entry_price: Decimal, stop_price: Decimal) -> int:
    """Return shares whose maximum stop-loss risk fits the risk budget."""

    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share <= 0:
        raise ValueError("entry_price and stop_price must differ")
    return int((capital * risk_fraction) // risk_per_share)
