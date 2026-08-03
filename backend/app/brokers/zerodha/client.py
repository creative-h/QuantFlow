"""Async HTTP client for the Kite Connect REST API."""

from typing import Any

import httpx


class KiteClient:
    """Small async client for supported Kite endpoints."""

    base_url = "https://api.kite.trade"

    def __init__(self, api_key: str, access_token: str | None = None) -> None:
        self._api_key = api_key
        self._access_token = access_token

    @property
    def headers(self) -> dict[str, str]:
        headers = {"X-Kite-Version": "3"}
        if self._access_token:
            headers["Authorization"] = f"token {self._api_key}:{self._access_token}"
        return headers

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an API request and raise for failed Kite responses."""

        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=15.0) as client:
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(payload.get("message", "Kite request failed"))
        return payload["data"]
