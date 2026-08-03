# QuantFlow

QuantFlow is a modular Python platform for historical research, backtesting, paper trading, and broker-routed execution. Broker adapters are separate from historical-data providers so the platform can work with Zerodha Kite Connect for account execution while using Yahoo Finance, NSE bhavcopies, CSV, or Parquet for market-data research.

## Quick start

1. Copy `backend/.env.example` to `backend/.env` and fill in a strong `SECRET_KEY`. Add Kite credentials only when you are ready to use its login flow.
2. Copy `.env.example` to `.env` if you need to override the local PostgreSQL credentials.
3. Start the stack: `docker compose up --build`.
4. Visit `http://localhost:8000/docs` for the API and `http://localhost:8501` for Streamlit.

For local development, use Python 3.12, create a virtual environment, install `backend/requirements.txt`, then run `uvicorn app.main:app --reload --port 8000` from `backend`.

## Kite Connect callback

Expose the backend with `ngrok http 8000`, then register the HTTPS tunnel address plus `/login` as the Redirect URL and `/postback` as the Postback URL in Kite Connect. Never put `ZERODHA_API_SECRET` or access tokens in the frontend.

## Quality commands

From `backend`, run `pytest`, `ruff check .`, and `black --check .`. Install hooks with `pre-commit install`.
