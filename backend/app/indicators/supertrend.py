"""Supertrend technical indicator."""

import pandas as pd

from app.indicators.atr import atr


def supertrend(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0
) -> pd.DataFrame:
    """Return Supertrend value and direction (+1 for uptrend, -1 for downtrend)."""
    atr_val = atr(high, low, close, period)
    hl2 = (high + low) / 2

    basic_upper = hl2 + (multiplier * atr_val)
    basic_lower = hl2 - (multiplier * atr_val)

    final_upper = pd.Series(0.0, index=close.index)
    final_lower = pd.Series(0.0, index=close.index)
    st = pd.Series(0.0, index=close.index)
    direction = pd.Series(1, index=close.index)

    for i in range(1, len(close)):
        # Final Upper Band calculation
        if (
            basic_upper.iloc[i] < final_upper.iloc[i - 1]
            or close.iloc[i - 1] > final_upper.iloc[i - 1]
        ):
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        # Final Lower Band calculation
        if (
            basic_lower.iloc[i] > final_lower.iloc[i - 1]
            or close.iloc[i - 1] < final_lower.iloc[i - 1]
        ):
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

        # Trend direction
        if direction.iloc[i - 1] == 1:
            if close.iloc[i] < final_lower.iloc[i]:
                direction.iloc[i] = -1
                st.iloc[i] = final_upper.iloc[i]
            else:
                direction.iloc[i] = 1
                st.iloc[i] = final_lower.iloc[i]
        else:
            if close.iloc[i] > final_upper.iloc[i]:
                direction.iloc[i] = 1
                st.iloc[i] = final_lower.iloc[i]
            else:
                direction.iloc[i] = -1
                st.iloc[i] = final_upper.iloc[i]

    return pd.DataFrame({"supertrend": st, "direction": direction})
