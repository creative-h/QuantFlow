"""Broker contract implemented by every execution provider."""

from abc import ABC, abstractmethod

from app.models.trading import Holding, Order, OrderRequest, Position, Profile


class Broker(ABC):
    """Abstract broker API, independent of any vendor SDK."""

    @abstractmethod
    async def login(self, request_token: str) -> str:
        """Exchange an authorization token and return an access token."""

    @abstractmethod
    async def place_order(self, order: OrderRequest) -> Order:
        """Place an order."""

    @abstractmethod
    async def cancel_order(self, order_id: str) -> Order:
        """Cancel an existing order."""

    @abstractmethod
    async def positions(self) -> list[Position]:
        """Return current positions."""

    @abstractmethod
    async def holdings(self) -> list[Holding]:
        """Return long-term holdings."""

    @abstractmethod
    async def orders(self) -> list[Order]:
        """Return orders."""

    @abstractmethod
    async def profile(self) -> Profile:
        """Return the authenticated account profile."""
