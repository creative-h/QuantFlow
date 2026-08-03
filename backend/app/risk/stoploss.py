"""Stop-loss level calculations."""

from decimal import Decimal


def fixed_stop_loss(entry_price: Decimal, loss_fraction: Decimal, is_long: bool = True) -> Decimal:
    """Return a fixed-percentage stop price."""

    multiplier = Decimal("1") - loss_fraction if is_long else Decimal("1") + loss_fraction
    return entry_price * multiplier
