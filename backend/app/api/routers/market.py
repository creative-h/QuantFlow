"""Market data API router."""

from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.api.dependencies import get_market_provider
from app.marketdata.storage import PartitionedParquetStorage
from app.marketdata.validator import DataValidationError

router = APIRouter(prefix="/market", tags=["market-data"])


@router.get("/history")
async def get_market_history(
    symbol: str = Query(..., description="Stock symbol (e.g. RELIANCE.NS or AAPL)"),
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    provider: str = Query("yfinance", description="Data provider: yfinance, csv, parquet"),
    interval: str = Query("1d", description="Candle interval (e.g. 1d, 1m, 5m, 1h)"),
    save_parquet: bool = Query(False, description="Persist fetched data as partitioned Parquet"),
) -> dict[str, Any]:
    """Retrieve normalized historical OHLCV market data."""
    logger.info(
        "GET /market/history request for symbol='{}', provider='{}', range={} to {}",
        symbol,
        provider,
        start,
        end,
    )

    if start > end:
        raise HTTPException(
            status_code=400, detail="Invalid date range: start date must be before end date"
        )

    try:
        data_provider = get_market_provider(provider)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    try:
        df = await data_provider.get_candles(
            symbol=symbol, start=start, end=end, interval=interval
        )
    except FileNotFoundError as err:
        logger.warning("Market data file not found: {}", str(err))
        raise HTTPException(
            status_code=404, detail=f"Market data not found for symbol '{symbol}'"
        ) from err
    except DataValidationError as err:
        logger.error("Market data validation error for '{}': {}", symbol, str(err))
        raise HTTPException(status_code=400, detail=f"Data validation failed: {err}") from err
    except Exception as err:
        logger.exception("Failed to fetch market data for '{}'", symbol)
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch market data: {err}"
        ) from err

    if df.empty:
        return {
            "status": "success",
            "symbol": symbol,
            "provider": provider,
            "interval": interval,
            "count": 0,
            "data": [],
        }

    # Optionally persist as partitioned parquet
    if save_parquet:
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent / "data" / "market"
            storage = PartitionedParquetStorage(base_dir)
            storage.save(df, symbol)
        except Exception as err:
            logger.error("Failed to save partitioned Parquet for '{}': {}", symbol, str(err))

    # Format records for JSON response
    records = []
    for ts, row in df.iterrows():
        records.append(
            {
                "timestamp": ts.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
        )

    return {
        "status": "success",
        "symbol": symbol,
        "provider": provider,
        "interval": interval,
        "count": len(records),
        "data": records,
    }
