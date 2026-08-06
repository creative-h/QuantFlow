"""Realistic Paper Broker calculating transaction costs, STT, GST, slippage, and execution delays."""

from dataclasses import dataclass
import time
from typing import Dict


@dataclass
class TradeExecutionCost:
    """Dataclass storing detailed transaction breakdown for a trade."""

    gross_price: float
    slippage: float
    executed_price: float
    brokerage: float  # Flat ₹20 per order
    stt: float  # 0.125% on sell side option premium
    exchange_charges: float  # 0.05%
    gst: float  # 18% on (brokerage + exchange charges)
    sebi_charges: float  # ₹10 per crore
    stamp_duty: float  # 0.003% on buy side
    total_charges: float
    execution_delay_ms: float


class RealisticBroker:
    """Realistic Paper Broker executing orders with realistic costs, slippage, and execution latency."""

    FLAT_BROKERAGE = 20.0  # ₹20 flat fee per order

    @classmethod
    def calculate_execution(
        cls,
        order_type: str,  # "BUY" or "SELL"
        price: float,
        quantity: int,
        slippage_pct: float = 0.05,
    ) -> TradeExecutionCost:
        """Calculate realistic order execution price, slippage, and complete statutory tax breakdown."""
        # 1. Slippage simulation (e.g. 0.05% adverse price movement)
        slip_direction = 1.0 if order_type == "BUY" else -1.0
        slippage = round(price * (slippage_pct / 100.0) * slip_direction, 2)
        exec_price = round(price + slippage, 2)

        turnover = exec_price * quantity

        # 2. Statutory Transaction Taxes & Charges
        stt = round(turnover * 0.00125, 2) if order_type == "SELL" else 0.0
        exch_charges = round(turnover * 0.0005, 2)
        gst = round((cls.FLAT_BROKERAGE + exch_charges) * 0.18, 2)
        sebi_charges = round(turnover * 0.000001, 2)
        stamp_duty = round(turnover * 0.00003, 2) if order_type == "BUY" else 0.0

        total_charges = round(cls.FLAT_BROKERAGE + stt + exch_charges + gst + sebi_charges + stamp_duty, 2)

        # 3. Execution delay simulation (50ms execution delay)
        exec_delay_ms = 50.0

        return TradeExecutionCost(
            gross_price=price,
            slippage=slippage,
            executed_price=exec_price,
            brokerage=cls.FLAT_BROKERAGE,
            stt=stt,
            exchange_charges=exch_charges,
            gst=gst,
            sebi_charges=sebi_charges,
            stamp_duty=stamp_duty,
            total_charges=total_charges,
            execution_delay_ms=exec_delay_ms,
        )
