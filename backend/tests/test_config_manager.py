"""Unit tests for YAML configuration files loading and structure."""

from pathlib import Path
import yaml


def test_strategies_yaml_loading():
    config_path = Path(__file__).parent.parent / "config" / "strategies.yaml"
    assert config_path.exists()
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    assert "default_strategy" in data
    assert len(data["active_strategies"]) >= 4


def test_risk_yaml_loading():
    config_path = Path(__file__).parent.parent / "config" / "risk.yaml"
    assert config_path.exists()
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["risk_parameters"]["max_position_size_pct"] == 10.0
    assert data["risk_parameters"]["daily_max_loss_limit"] == 5000.0


def test_ai_yaml_loading():
    config_path = Path(__file__).parent.parent / "config" / "ai.yaml"
    assert config_path.exists()
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["ai_consensus"]["min_confidence_threshold"] == 75.0
    assert "agent_weights" in data["ai_consensus"]


def test_market_yaml_loading():
    config_path = Path(__file__).parent.parent / "config" / "market.yaml"
    assert config_path.exists()
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    assert "NIFTY" in data["market_feed"]["primary_indices"]
    assert data["market_feed"]["strike_step_mapping"]["NIFTY"] == 50.0


def test_paper_yaml_loading():
    config_path = Path(__file__).parent.parent / "config" / "paper.yaml"
    assert config_path.exists()
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["paper_trading"]["initial_cash"] == 100000.0
    assert data["paper_trading"]["lot_sizes"]["NIFTY"] == 25
