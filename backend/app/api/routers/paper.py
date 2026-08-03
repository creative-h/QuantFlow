"""FastAPI Router managing Live Paper Trading Engine lifecycle and telemetry."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_live_paper_engine
from app.paper.live_engine import LivePaperEngine, LivePaperSessionConfig

router = APIRouter(prefix="/paper", tags=["Live Paper Trading"])


class StartPaperSessionRequest(BaseModel):
    symbols: List[str] = Field(default_factory=lambda: ["AAPL", "MSFT"])
    strategy_names: List[str] = Field(default_factory=lambda: ["ema"])
    poll_interval_seconds: int = 5
    initial_cash: float = 100000.0
    auto_eod_report: bool = True


class DemoOrderRequest(BaseModel):
    symbol: str = "NIFTY"
    side: str = "BUY"
    quantity: int = 10
    price: Optional[float] = 100.0


@router.get("/status")
async def get_paper_status(
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> Dict[str, Any]:
    """Get live paper engine status, active strategies, cash, equity, and PnL metrics."""
    broker = engine.broker
    portfolio = broker.portfolio if broker else None

    return {
        "state": engine.state.value,
        "config": engine.config.__dict__ if engine.config else None,
        "active_strategies": list(engine.active_strategies.keys()),
        "cash": float(portfolio.cash)
        if portfolio
        else (engine.config.initial_cash if engine.config else 0.0),
        "total_equity": float(portfolio.total_equity) if portfolio else 0.0,
        "realized_pnl": float(portfolio.total_realized_pnl) if portfolio else 0.0,
        "unrealized_pnl": float(portfolio.total_unrealized_pnl) if portfolio else 0.0,
        "drawdown_pct": portfolio.drawdown_pct if portfolio else 0.0,
    }


@router.get("/positions")
async def get_paper_positions(
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> List[Dict[str, Any]]:
    """Get active positions in live paper session."""
    if not engine.broker:
        return []
    positions = await engine.broker.positions()
    return [
        {
            "symbol": pos.symbol,
            "quantity": pos.quantity,
            "average_price": float(pos.average_price),
            "last_price": float(pos.last_price),
        }
        for pos in positions
    ]


@router.get("/orders")
async def get_paper_orders(
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> List[Dict[str, Any]]:
    """Get history of paper orders."""
    if not engine.broker:
        return []
    orders = await engine.broker.orders()
    return [
        {
            "id": o.id,
            "symbol": o.request.symbol,
            "side": o.request.side.value,
            "quantity": o.request.quantity,
            "status": o.status.value,
            "average_price": float(o.average_price) if o.average_price else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_paper_session(
    body: StartPaperSessionRequest,
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> Dict[str, Any]:
    """Start live paper trading session."""
    config = LivePaperSessionConfig(
        symbols=body.symbols,
        strategy_names=body.strategy_names,
        poll_interval_seconds=body.poll_interval_seconds,
        initial_cash=body.initial_cash,
        auto_eod_report=body.auto_eod_report,
    )

    engine.start(config)
    return {"message": "Live paper session started", "state": engine.state.value}


@router.post("/stop")
async def stop_paper_session(
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> Dict[str, Any]:
    """Stop live paper session and return EOD report summary."""
    report_summary = await engine.stop()
    return {"message": "Live paper session stopped", "report_summary": report_summary}


@router.post("/pause")
async def pause_paper_session(
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> Dict[str, Any]:
    """Pause live paper session poller loop."""
    engine.pause()
    return {"message": "Live paper session paused", "state": engine.state.value}


@router.post("/resume")
async def resume_paper_session(
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> Dict[str, Any]:
    """Resume paused live paper session poller loop."""
    engine.resume()
    return {"message": "Live paper session resumed", "state": engine.state.value}


@router.post("/demo-order")
async def inject_demo_order(
    body: DemoOrderRequest,
    engine: LivePaperEngine = Depends(get_live_paper_engine),
) -> Dict[str, Any]:
    """Inject a demo paper order to test full execution pipeline instantly."""
    order = await engine.inject_demo_order(
        symbol=body.symbol, side_str=body.side, quantity=body.quantity, price=body.price
    )
    return {
        "message": "Demo order injected successfully",
        "order_id": order.id,
        "symbol": order.request.symbol,
        "side": order.request.side.value,
        "status": order.status.value,
        "average_price": float(order.average_price) if order.average_price else None,
    }
