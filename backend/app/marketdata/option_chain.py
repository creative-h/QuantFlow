"""Option Chain Engine for Indian index options (NIFTY, BANKNIFTY, FINNIFTY, SENSEX)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class OptionContract:
    """Dataclass representing an individual Call (CE) or Put (PE) option contract."""

    symbol: str
    underlying: str
    strike: float
    option_type: str  # "CE" or "PE"
    ltp: float  # Last Traded Price (Premium)
    iv: float  # Implied Volatility %
    oi: int  # Open Interest
    oi_change: float  # OI Change %
    delta: float  # Option Delta
    gamma: float = 0.0012
    theta: float = -12.5


@dataclass
class OptionChain:
    """Dataclass representing full option chain matrix around spot price."""

    underlying_symbol: str
    spot_price: float
    atm_strike: float
    pcr: float  # Put-Call Ratio
    calls: Dict[float, OptionContract] = field(default_factory=dict)
    puts: Dict[float, OptionContract] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_atm_call(self) -> Optional[OptionContract]:
        return self.calls.get(self.atm_strike)

    def get_atm_put(self) -> Optional[OptionContract]:
        return self.puts.get(self.atm_strike)


class OptionChainEngine:
    """Engine computing live/simulated option chain matrix, ATM strikes, and Greeks."""

    STRIKE_STEPS = {
        "NIFTY": 50.0,
        "NIFTY 50": 50.0,
        "BANKNIFTY": 100.0,
        "FINNIFTY": 50.0,
        "SENSEX": 100.0,
    }

    @classmethod
    def get_strike_step(cls, symbol: str) -> float:
        return cls.STRIKE_STEPS.get(symbol.upper(), 50.0)

    @classmethod
    def calculate_atm_strike(cls, symbol: str, spot_price: float) -> float:
        step = cls.get_strike_step(symbol)
        return round(spot_price / step) * step

    @classmethod
    def generate_chain(
        cls, underlying_symbol: str, spot_price: float, num_strikes: int = 5
    ) -> OptionChain:
        """Generate structured option chain centered around ATM strike."""
        sym_clean = underlying_symbol.upper()
        step = cls.get_strike_step(sym_clean)
        atm_strike = cls.calculate_atm_strike(sym_clean, spot_price)

        strikes = [atm_strike + (i * step) for i in range(-num_strikes, num_strikes + 1)]

        calls: Dict[float, OptionContract] = {}
        puts: Dict[float, OptionContract] = {}

        total_call_oi = 0
        total_put_oi = 0

        for strike in strikes:
            # Synthetic premium calculation (Intrinsic + Time Value)
            call_intrinsic = max(0.0, spot_price - strike)
            put_intrinsic = max(0.0, strike - spot_price)

            time_val = max(15.0, 120.0 - abs(spot_price - strike) * 0.4)
            call_ltp = round(call_intrinsic + time_val, 2)
            put_ltp = round(put_intrinsic + time_val, 2)

            # Delta estimation
            dist = (spot_price - strike) / step
            call_delta = round(max(0.05, min(0.95, 0.50 + dist * 0.10)), 2)
            put_delta = round(call_delta - 1.0, 2)

            call_oi = int(max(10000, 150000 - abs(dist) * 20000))
            put_oi = int(max(12000, 180000 - abs(dist) * 22000))

            total_call_oi += call_oi
            total_put_oi += put_oi

            calls[strike] = OptionContract(
                symbol=f"{sym_clean}_{int(strike)}_CE",
                underlying=sym_clean,
                strike=strike,
                option_type="CE",
                ltp=call_ltp,
                iv=14.5,
                oi=call_oi,
                oi_change=4.2,
                delta=call_delta,
            )

            puts[strike] = OptionContract(
                symbol=f"{sym_clean}_{int(strike)}_PE",
                underlying=sym_clean,
                strike=strike,
                option_type="PE",
                ltp=put_ltp,
                iv=15.2,
                oi=put_oi,
                oi_change=6.1,
                delta=put_delta,
            )

        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0

        return OptionChain(
            underlying_symbol=sym_clean,
            spot_price=spot_price,
            atm_strike=atm_strike,
            pcr=pcr,
            calls=calls,
            puts=puts,
        )
