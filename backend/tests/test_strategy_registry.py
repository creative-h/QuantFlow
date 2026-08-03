"""Unit tests for StrategyRegistry and dynamic plugin discovery."""

import pytest

from app.strategies.base import Strategy
from app.strategies.ema_crossover import EMACrossoverStrategy
from app.strategies.registry import StrategyMetadata, StrategyRegistry


def test_strategy_registry_register_and_load():
    StrategyRegistry.register("test_ema", EMACrossoverStrategy)
    loaded_cls = StrategyRegistry.load("test_ema")
    assert loaded_cls == EMACrossoverStrategy
    assert "test_ema" in StrategyRegistry.list_strategies()


def test_strategy_registry_load_case_insensitive():
    StrategyRegistry.register("test_case", EMACrossoverStrategy)
    loaded_cls = StrategyRegistry.load("TEST_CASE")
    assert loaded_cls == EMACrossoverStrategy


def test_strategy_registry_instantiate():
    inst = StrategyRegistry.instantiate("test_ema", fast_period=5, slow_period=15)
    assert isinstance(inst, EMACrossoverStrategy)
    assert inst.fast_period == 5
    assert inst.slow_period == 15


def test_strategy_registry_unregister():
    StrategyRegistry.register("temp_strat", EMACrossoverStrategy)
    assert "temp_strat" in StrategyRegistry.list_strategies()
    unreg_ok = StrategyRegistry.unregister("temp_strat")
    assert unreg_ok is True
    assert "temp_strat" not in StrategyRegistry.list_strategies()


def test_strategy_registry_metadata():
    meta = StrategyMetadata(name="Custom", description="Custom strategy description")
    StrategyRegistry.register("custom_meta", EMACrossoverStrategy, metadata=meta)
    retrieved_meta = StrategyRegistry.get_metadata("custom_meta")
    assert retrieved_meta is not None
    assert retrieved_meta.name == "Custom"
    assert retrieved_meta.description == "Custom strategy description"


def test_strategy_registry_metadata_nonexistent():
    assert StrategyRegistry.get_metadata("nonexistent_strategy_xyz") is None


def test_strategy_registry_auto_discovery():
    StrategyRegistry.discover_strategies()
    registered = StrategyRegistry.list_strategies()
    assert len(registered) > 0
    assert "ema" in registered or "supertrend" in registered or "vwap" in registered


def test_strategy_registry_invalid_type_raises_error():
    class DummyNotStrategy:
        pass

    with pytest.raises(TypeError, match="must inherit from Strategy"):
        StrategyRegistry.register("invalid", DummyNotStrategy)
