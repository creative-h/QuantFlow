"""FastAPI dependency providers."""

from pathlib import Path

from fastapi import Depends

from app.brokers.zerodha.broker import ZerodhaBroker
from app.core.config import Settings, get_settings
from app.marketdata.base import MarketDataProvider
from app.marketdata.csv_provider import CSVProvider
from app.marketdata.parquet_provider import ParquetProvider
from app.marketdata.yfinance_provider import YahooFinanceProvider
from app.services.zerodha_auth import ZerodhaAuthService


def get_zerodha_broker(settings: Settings = Depends(get_settings)) -> ZerodhaBroker:
    """Provide a configured, unauthenticated Kite broker adapter."""
    return ZerodhaBroker(settings)


def get_zerodha_auth_service(settings: Settings = Depends(get_settings)) -> ZerodhaAuthService:
    """Provide a configured ZerodhaAuthService instance."""
    return ZerodhaAuthService(settings)


def get_market_provider(provider: str = "yfinance") -> MarketDataProvider:
    """Factory dependency for market data providers."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "market"
    provider_key = provider.lower()

    if provider_key in ("yfinance", "yahoo"):
        return YahooFinanceProvider()
    elif provider_key == "csv":
        return CSVProvider(directory=data_dir)
    elif provider_key == "parquet":
        return ParquetProvider(directory=data_dir)
    else:
        raise ValueError(f"Unsupported market data provider: '{provider}'")
