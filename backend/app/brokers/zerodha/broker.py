"""Broker implementation backed by Kite Connect."""

from app.brokers.base import Broker
from app.brokers.zerodha.auth import KiteAuthService
from app.brokers.zerodha.client import KiteClient
from app.brokers.zerodha.orders import to_domain_order, to_order
from app.brokers.zerodha.portfolio import to_holding, to_position, to_profile
from app.core.config import Settings
from app.models.trading import Holding, Order, OrderRequest, Position, Profile


class ZerodhaBroker(Broker):
    """Kite Connect adapter limited to account and order operations."""

    def __init__(self, settings: Settings, access_token: str | None = None) -> None:
        self._settings = settings
        self._client = KiteClient(settings.zerodha_api_key, access_token)

    async def login(self, request_token: str) -> str:
        return await KiteAuthService(self._settings).exchange_request_token(request_token)

    async def place_order(self, order: OrderRequest) -> Order:
        data = await self._client.request(
            "POST",
            "/orders/regular",
            data={
                "exchange": "NSE",
                "tradingsymbol": order.symbol,
                "transaction_type": order.side.value,
                "quantity": order.quantity,
                "order_type": order.order_type.value,
                "product": "CNC",
                **({"price": str(order.price)} if order.price else {}),
            },
        )
        return to_order(data, order)

    async def cancel_order(self, order_id: str) -> Order:
        await self._client.request("DELETE", f"/orders/regular/{order_id}")
        cancelled = next((order for order in await self.orders() if order.id == order_id), None)
        if cancelled is None:
            raise RuntimeError(f"Cancelled order {order_id} was not returned by Kite")
        return cancelled

    async def positions(self) -> list[Position]:
        data = await self._client.request("GET", "/portfolio/positions")
        return [to_position(item) for item in data["net"]]

    async def holdings(self) -> list[Holding]:
        data = await self._client.request("GET", "/portfolio/holdings")
        return [to_holding(item) for item in data]

    async def orders(self) -> list[Order]:
        data = await self._client.request("GET", "/orders")
        return [to_domain_order(item) for item in data]

    async def profile(self) -> Profile:
        return to_profile(await self._client.request("GET", "/user/profile"))
