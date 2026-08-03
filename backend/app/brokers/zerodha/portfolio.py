"""Kite portfolio response translators."""

from decimal import Decimal

from app.models.trading import Holding, Position, Profile


def to_position(item: dict[str, object]) -> Position:
    return Position(symbol=str(item["tradingsymbol"]), quantity=int(item["quantity"]), average_price=Decimal(str(item["average_price"])))


def to_holding(item: dict[str, object]) -> Holding:
    return Holding(symbol=str(item["tradingsymbol"]), quantity=int(item["quantity"]), average_price=Decimal(str(item["average_price"])))


def to_profile(item: dict[str, object]) -> Profile:
    return Profile(user_id=str(item["user_id"]), user_name=str(item["user_name"]), email=str(item.get("email") or "") or None)
