"""Entry Engine supporting single entry orders and progressive Scaling In tranches."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class EntryTranche:
    """Dataclass storing details for a single entry tranche."""

    tranche_id: int
    price: float
    quantity: int
    timestamp: datetime = field(default_factory=datetime.now)


class EntryEngine:
    """Entry Engine managing initial positions and progressive Scaling In tranches."""

    def __init__(self, target_quantity: int = 100, num_tranches: int = 2) -> None:
        self.target_quantity = target_quantity
        self.num_tranches = num_tranches
        self.tranches: List[EntryTranche] = []

    def execute_initial_entry(self, price: float, quantity: int) -> EntryTranche:
        """Execute initial position entry."""
        tranche = EntryTranche(tranche_id=1, price=price, quantity=quantity)
        self.tranches.append(tranche)
        return tranche

    def execute_scale_in(self, price: float, quantity: int) -> EntryTranche:
        """Execute subsequent Scaling In entry tranche."""
        tranche_id = len(self.tranches) + 1
        tranche = EntryTranche(tranche_id=tranche_id, price=price, quantity=quantity)
        self.tranches.append(tranche)
        return tranche

    def get_average_entry_price(self) -> float:
        """Calculate weighted average entry price across all tranches."""
        if not self.tranches:
            return 0.0
        total_cost = sum(t.price * t.quantity for t in self.tranches)
        total_qty = sum(t.quantity for t in self.tranches)
        return round(total_cost / total_qty, 2) if total_qty > 0 else 0.0

    def get_total_quantity(self) -> int:
        """Calculate total accumulated quantity across all tranches."""
        return sum(t.quantity for t in self.tranches)
