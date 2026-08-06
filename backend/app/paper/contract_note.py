"""Zerodha Contract Note Calculator computing statutory taxes, STT, GST, SEBI fees, and Net Realized PnL."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ZerodhaContractNote:
    """Dataclass storing exact Zerodha contract note statutory tax breakdown."""

    gross_pnl: float
    buy_turnover: float
    sell_turnover: float
    total_turnover: float
    flat_brokerage: float  # ₹40 (₹20 buy + ₹20 sell)
    stt: float  # 0.125% on option sell turnover
    exchange_turnover_charge: float  # 0.05%
    gst: float  # 18% on (brokerage + exchange charges)
    sebi_turnover_charge: float  # ₹10 per Cr
    stamp_duty: float  # 0.003% on buy turnover
    total_tax_charges: float
    net_realized_pnl: float


class ZerodhaContractNoteCalculator:
    """Zerodha Contract Note Calculator calculating statutory transaction costs."""

    FLAT_PER_ORDER_BROKERAGE = 20.0

    @classmethod
    def calculate_contract_note(
        cls,
        buy_price: float,
        sell_price: float,
        quantity: int,
    ) -> ZerodhaContractNote:
        """Calculate complete Zerodha Contract Note statutory tax breakdown."""
        buy_turnover = round(buy_price * quantity, 2)
        sell_turnover = round(sell_price * quantity, 2)
        total_turnover = round(buy_turnover + sell_turnover, 2)
        gross_pnl = round(sell_turnover - buy_turnover, 2)

        brokerage = cls.FLAT_PER_ORDER_BROKERAGE * 2.0  # Buy + Sell
        stt = round(sell_turnover * 0.00125, 2)
        exch_charges = round(total_turnover * 0.0005, 2)
        gst = round((brokerage + exch_charges) * 0.18, 2)
        sebi_charges = round(total_turnover * 0.000001, 2)
        stamp_duty = round(buy_turnover * 0.00003, 2)

        total_charges = round(brokerage + stt + exch_charges + gst + sebi_charges + stamp_duty, 2)
        net_pnl = round(gross_pnl - total_charges, 2)

        return ZerodhaContractNote(
            gross_pnl=gross_pnl,
            buy_turnover=buy_turnover,
            sell_turnover=sell_turnover,
            total_turnover=total_turnover,
            flat_brokerage=brokerage,
            stt=stt,
            exchange_turnover_charge=exch_charges,
            gst=gst,
            sebi_turnover_charge=sebi_charges,
            stamp_duty=stamp_duty,
            total_tax_charges=total_charges,
            net_realized_pnl=net_pnl,
        )
