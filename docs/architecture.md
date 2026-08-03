# Architecture

QuantFlow follows ports-and-adapters boundaries. Strategies depend on canonical OHLCV frames, market-data providers implement the provider port, and brokers implement the broker port. Backtesting and paper execution therefore do not depend on Kite Connect. The API layer composes configuration and adapters through FastAPI dependencies.

PostgreSQL is the operational database. SQLAlchemy owns connection/session lifecycle and Alembic owns schema migrations. Logs are written to daily-rotated application and error files with a 30-day retention period.
