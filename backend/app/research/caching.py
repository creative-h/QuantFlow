"""SQLite-backed research caching system for market data, indicators, and optimization results."""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from loguru import logger


class ResearchCache:
    """Persistent SQLite cache for market data, indicator computations, and optimization runs."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data" / "cache"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "research_cache.db"
        else:
            self.db_path = Path(db_path)
            if self.db_path.parent:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_cache (
                    cache_key TEXT PRIMARY KEY,
                    data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS result_cache (
                    cache_key TEXT PRIMARY KEY,
                    result_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @staticmethod
    def _make_key(*args: Any) -> str:
        raw = json.dumps([str(a) for a in args], sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_dataframe(self, key_prefix: str, *args: Any) -> Optional[pd.DataFrame]:
        """Retrieve cached DataFrame or None."""
        cache_key = f"{key_prefix}_{self._make_key(*args)}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_json FROM data_cache WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                logger.debug("Cache HIT for DataFrame key: {}", cache_key[:12])
                return pd.read_json(row[0], orient="split")
        logger.debug("Cache MISS for DataFrame key: {}", cache_key[:12])
        return None

    def set_dataframe(self, df: pd.DataFrame, key_prefix: str, *args: Any) -> None:
        """Cache a pandas DataFrame."""
        cache_key = f"{key_prefix}_{self._make_key(*args)}"
        json_data = df.to_json(orient="split", date_format="iso")
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO data_cache (cache_key, data_json) VALUES (?, ?)",
                (cache_key, json_data),
            )
            logger.debug("Cached DataFrame under key: {}", cache_key[:12])

    def get_result(self, key_prefix: str, *args: Any) -> Optional[Dict[str, Any]]:
        """Retrieve cached result dict or None."""
        cache_key = f"{key_prefix}_{self._make_key(*args)}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT result_json FROM result_cache WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                logger.debug("Cache HIT for result key: {}", cache_key[:12])
                return json.loads(row[0])
        return None

    def set_result(self, result: Dict[str, Any], key_prefix: str, *args: Any) -> None:
        """Cache a result dictionary."""
        cache_key = f"{key_prefix}_{self._make_key(*args)}"
        json_data = json.dumps(result)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO result_cache (cache_key, result_json) VALUES (?, ?)",
                (cache_key, json_data),
            )
            logger.debug("Cached result under key: {}", cache_key[:12])

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM data_cache")
            conn.execute("DELETE FROM result_cache")
            logger.info("ResearchCache cleared")
