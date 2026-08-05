"""Unit tests for KiteLiveClient."""

import pytest

from app.marketdata.kite_live import KiteLiveClient


def test_kite_live_client_initialization():
    client = KiteLiveClient()
    assert client.auth_session is not None


def test_kite_live_client_get_quote():
    client = KiteLiveClient()
    quotes = client.get_quote(["NIFTY", "BANKNIFTY"])
    assert "NIFTY" in quotes
    assert quotes["NIFTY"]["last_price"] > 0.0


def test_kite_live_client_get_instruments():
    client = KiteLiveClient()
    insts = client.get_instruments("NFO")
    assert isinstance(insts, list)
