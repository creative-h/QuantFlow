"""Unit tests for /paper/* REST API endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def test_paper_status_endpoint():
    response = client.get("/paper/status")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "cash" in data
    assert "total_equity" in data


def test_paper_positions_and_orders_endpoints():
    pos_res = client.get("/paper/positions")
    assert pos_res.status_code == 200
    assert isinstance(pos_res.json(), list)

    ord_res = client.get("/paper/orders")
    assert ord_res.status_code == 200
    assert isinstance(ord_res.json(), list)


def test_paper_start_pause_resume_stop_flow():
    payload = {
        "symbols": ["AAPL"],
        "strategy_names": ["ema"],
        "poll_interval_seconds": 10,
        "initial_cash": 100000.0,
        "auto_eod_report": True,
    }

    start_res = client.post("/paper/start", json=payload)
    assert start_res.status_code == 200
    assert start_res.json()["state"] == "RUNNING"

    pause_res = client.post("/paper/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["state"] == "PAUSED"

    resume_res = client.post("/paper/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["state"] == "RUNNING"

    stop_res = client.post("/paper/stop")
    assert stop_res.status_code == 200
    assert "message" in stop_res.json()


def test_paper_demo_order_endpoint():
    demo_payload = {
        "symbol": "NIFTY",
        "side": "BUY",
        "quantity": 10,
        "price": 25000.0,
    }
    res = client.post("/paper/demo-order", json=demo_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Demo order injected successfully"
    assert data["symbol"] == "NIFTY"
    assert data["side"] == "BUY"
    assert "order_id" in data
