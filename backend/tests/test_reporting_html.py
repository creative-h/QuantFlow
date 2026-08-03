"""Unit tests for HTMLReportGenerator, JSONReportGenerator, and YAML config loader."""

from decimal import Decimal

import pytest

from app.analytics.reporting import HTMLReportGenerator, JSONReportGenerator
from app.core.config_loader import load_strategy_yaml
from app.models.trading import Side
from app.paper.portfolio.portfolio import ProfessionalPortfolio


def test_html_and_json_report_generators(tmp_path):
    port = ProfessionalPortfolio(initial_cash=50000.0)
    port.record_fill("1", "AAPL", Side.BUY, 10, Decimal("150.0"))
    port.update_market_price("AAPL", Decimal("160.0"))
    port.record_fill("2", "AAPL", Side.SELL, 10, Decimal("160.0"))

    html_file = tmp_path / "report.html"
    json_file = tmp_path / "report.json"

    html_out = HTMLReportGenerator.generate(port, title="Test Report", filepath=html_file)
    assert "<html" in html_out
    assert html_file.exists()

    json_out = JSONReportGenerator.generate(port, filepath=json_file)
    assert json_out["total_equity"] == 50100.0
    assert len(json_out["trades"]) == 2
    assert json_file.exists()


def test_load_strategy_yaml():
    cfg = load_strategy_yaml("ema")
    assert isinstance(cfg, dict)
    assert cfg.get("name") == "ema"
    assert "parameters" in cfg
