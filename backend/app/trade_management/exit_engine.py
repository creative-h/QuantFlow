"""Exit Engine supporting full position closures and progressive Scaling Out partial exits."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ExitTranche:
    """Dataclass storing details for a single exit tranche."""

    tranche_id: int
    price: float
    quantity: int
    reason: str  # e.g. "TARGET_1", "STOP_LOSS", "TIME_STOP"
    timestamp: datetime = field(default_factory=datetime.now)


class ExitEngine:
    """Exit Engine managing full position closures and progressive Scaling Out partial exits."""

    def __init__(self) -> None:
        self.exits: List[ExitTranche] = []

    def execute_partial_exit(self, price: float, quantity: int, reason: str = "PARTIAL_PROFIT") -> ExitTranche:
        """Execute Scaling Out partial profit exit."""
        tranche_id = len(self.exits) + 1
        tranche = ExitTranche(tranche_id=tranche_id, price=price, quantity=quantity, reason=reason)
        self.exits.append(tranche)
        return tranche

    def get_realized_pnl(self, avg_entry_price: float) -> float:
        """Calculate total realized PnL across all exit tranches."""
        if not self.exits or avg_entry_price <= 0:
            return 0.0
        return round(sum((t.price - avg_entry_price) * t.quantity for t in self.exits), 2)

    def get_total_exited_quantity(self) -> int:
        """Calculate total exited quantity across all exit tranches."""
        return sum(t.quantity for t in self.exits)
