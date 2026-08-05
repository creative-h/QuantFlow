"""Target Manager handling Multi-Target scaling (T1/T2/T3), Partial Profit Booking, and Move SL to Cost."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TargetStatus:
    """Dataclass storing status of a target level."""

    target_id: int  # 1, 2, 3
    target_price: float
    allocation_pct: float  # e.g. 50.0 for T1, 30.0 for T2, 20.0 for T3
    is_hit: bool = False
    hit_timestamp: Optional[datetime] = None


class TargetManager:
    """Target Manager executing multi-target exits and automatic Move SL to Cost (Break-even Engine)."""

    def __init__(
        self,
        entry_price: float,
        stop_loss: float,
        t1: float,
        t2: float,
        t3: float,
        move_sl_to_cost_on_t1: bool = True,
    ) -> None:
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.current_stop_loss = stop_loss
        self.move_sl_to_cost_on_t1 = move_sl_to_cost_on_t1

        self.targets = [
            TargetStatus(target_id=1, target_price=t1, allocation_pct=50.0),
            TargetStatus(target_id=2, target_price=t2, allocation_pct=30.0),
            TargetStatus(target_id=3, target_price=t3, allocation_pct=20.0),
        ]

    def check_targets(self, current_price: float) -> List[Dict]:
        """Check if current price hits T1, T2, or T3 and shift SL to Break-Even on T1."""
        triggered = []

        for tgt in self.targets:
            if not tgt.is_hit and current_price >= tgt.target_price:
                tgt.is_hit = True
                tgt.hit_timestamp = datetime.now()

                # Break-even Engine: Move SL to Cost upon hitting Target 1
                if tgt.target_id == 1 and self.move_sl_to_cost_on_t1:
                    self.current_stop_loss = max(self.current_stop_loss, self.entry_price)

                triggered.append(
                    {
                        "target_id": tgt.target_id,
                        "target_price": tgt.target_price,
                        "allocation_pct": tgt.allocation_pct,
                        "new_stop_loss": self.current_stop_loss,
                        "sl_moved_to_cost": (tgt.target_id == 1 and self.move_sl_to_cost_on_t1),
                    }
                )

        return triggered
