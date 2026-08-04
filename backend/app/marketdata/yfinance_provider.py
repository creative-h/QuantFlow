"""Yahoo Finance historical-data provider with NaN cleaning and symbol mapping."""

import asyncio
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger

from app.marketdata.base import MarketDataProvider
from app.marketdata.validator import validate_ohlcv


class YahooFinanceProvider(MarketDataProvider):
    """Fetch adjusted historical candles from Yahoo Finance with retries, NaN cleaning, and validation."""

    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
        "NIFTY 50": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "NIFTYBANK": "^NSEBANK",
        "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
        "SENSEX": "^BSESN",
        "INDIAVIX": "^INDIAVIX",
        "INDIA VIX": "^INDIAVIX",
    }

    def __init__(self, max_retries: int = 3, retry_delay: float = 0.5) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def get_candles(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        period: Optional[str] = "1mo",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch historical candles with symbol mapping, NaN cleaning, retry logic, and schema validation."""
        target_symbol = self.SYMBOL_MAP.get(symbol.upper(), symbol)
        logger.info(
            "Fetching Yahoo Finance candles for symbol '{}' (mapped: '{}') [period: {}, interval: {}]",
            symbol,
            target_symbol,
            period,
            interval,
        )

        last_exception: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                data = await asyncio.to_thread(
                    yf.download,
                    target_symbol,
                    start=start,
                    end=end,
                    period=period if (start is None and end is None) else None,
                    interval=interval,
                    auto_adjust=True,
                    progress=False,
                )
                if data is None or data.empty:
                    raise ValueError(f"No Yahoo Finance data returned for symbol '{target_symbol}'")

                # Handle MultiIndex columns if returned by yfinance
                if isinstance(data.columns, pd.MultiIndex):
                    data = data.xs(target_symbol, axis=1, level=1) if target_symbol in data.columns.levels[1] else data.droplevel(1, axis=1)

                # Clean incomplete rows containing NaN in key OHLC columns
                ohlc_cols = [c for c in ["Open", "High", "Low", "Close", "open", "high", "low", "close"] if c in data.columns]
                if ohlc_cols:
                    data = data.dropna(subset=ohlc_cols)

                if data.empty:
                    raise ValueError(f"Data for '{target_symbol}' empty after dropping NaN rows")

                validated = validate_ohlcv(data)
                logger.info(
                    "Successfully fetched and validated {} candles for '{}'",
                    len(validated),
                    symbol,
                )
                return validated

            except Exception as err:
                last_exception = err
                logger.warning(
                    "Attempt {}/{} failed fetching Yahoo Finance data for '{}': {}",
                    attempt,
                    self.max_retries,
                    symbol,
                    str(err),
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)

        logger.error(
            "Failed all {} attempts to fetch Yahoo Finance data for '{}'", self.max_retries, symbol
        )
        raise RuntimeError(
            f"Failed to fetch market data for '{symbol}' after {self.max_retries} attempts: {last_exception}"
        ) from last_exception
