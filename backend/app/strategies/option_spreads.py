"""Option Spread Engine constructing defined-risk multi-leg option spread strategies."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class OptionLeg:
    """Dataclass storing individual option leg parameters."""

    symbol: str
    strike: float
    option_type: str  # "CE", "PE"
    side: str  # "BUY", "SELL"
    quantity: int
    entry_price: float
    iv: float
    delta: float


@dataclass
class MultiLegOptionSpread:
    """Dataclass storing multi-leg defined-risk option spread strategy details."""

    strategy_name: str  # "BULL_CALL_SPREAD", "BEAR_PUT_SPREAD", "IRON_CONDOR"
    underlying: str
    spot_price: float
    expiry: str
    legs: List[OptionLeg]
    net_debit: float
    max_loss: float
    max_profit: float
    breakeven_point: float
    margin_required: float
    risk_reward_ratio: str
    win_probability: float


class OptionSpreadEngine:
    """Option Spread Engine constructing defined-risk multi-leg spreads."""

    @classmethod
    def construct_bull_call_spread(
        cls,
        spot: float = 24914.81,
        lot_size: int = 65,
        num_lots: int = 2,
    ) -> MultiLegOptionSpread:
        """Construct defined-risk Bull Call Spread (Buy ATM Call + Sell OTM Call)."""
        atm_strike = int(round(spot / 50.0) * 50)
        otm_strike = atm_strike + 200
        qty = lot_size * num_lots
        curr_month = datetime.now().strftime("%b")

        leg_buy = OptionLeg(
            symbol=f"28th {curr_month} {atm_strike} CE",
            strike=float(atm_strike),
            option_type="CE",
            side="BUY",
            quantity=qty,
            entry_price=120.00,
            iv=13.2,
            delta=0.55,
        )
        leg_sell = OptionLeg(
            symbol=f"28th {curr_month} {otm_strike} CE",
            strike=float(otm_strike),
            option_type="CE",
            side="SELL",
            quantity=-qty,
            entry_price=45.00,
            iv=12.5,
            delta=0.25,
        )

        net_debit_per_unit = round(leg_buy.entry_price - leg_sell.entry_price, 2)  # ₹75.00
        max_loss_total = round(net_debit_per_unit * qty, 2)  # ₹9,750.00
        max_profit_total = round((200.0 - net_debit_per_unit) * qty, 2)  # ₹16,250.00
        breakeven = round(atm_strike + net_debit_per_unit, 2)

        return MultiLegOptionSpread(
            strategy_name="BULL_CALL_SPREAD",
            underlying="NIFTY",
            spot_price=spot,
            expiry=f"28th {curr_month}",
            legs=[leg_buy, leg_sell],
            net_debit=net_debit_per_unit,
            max_loss=max_loss_total,
            max_profit=max_profit_total,
            breakeven_point=breakeven,
            margin_required=42000.00,  # SPAN Margin benefit applied
            risk_reward_ratio="1:1.67",
            win_probability=74.5,
        )
