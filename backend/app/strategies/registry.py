"""Strategy Registry and dynamic plugin discovery system."""

import importlib
import inspect
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from loguru import logger

from app.strategies.base import Strategy


@dataclass
class StrategyMetadata:
    """Metadata describing a strategy plugin."""

    name: str
    version: str = "1.0.0"
    author: str = "QuantFlow Community"
    description: str = "Quantitative trading strategy"
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeframes: List[str] = field(default_factory=lambda: ["1d", "1h", "5m"])
    supported_symbols: List[str] = field(default_factory=lambda: ["ALL"])


class StrategyRegistry:
    """Central registry managing strategy plugins with dynamic discovery."""

    _registry: Dict[str, Type[Strategy]] = {}
    _metadata: Dict[str, StrategyMetadata] = {}

    @classmethod
    def register(
        cls,
        name: str,
        strategy_cls: Type[Strategy],
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """Register a strategy class under a unique name."""
        if not issubclass(strategy_cls, Strategy):
            raise TypeError(
                f"Class '{strategy_cls.__name__}' must inherit from Strategy base class"
            )

        key = name.lower().strip()
        cls._registry[key] = strategy_cls
        cls._metadata[key] = metadata or StrategyMetadata(
            name=name,
            description=strategy_cls.__doc__ or "No description provided",
        )
        logger.info("Registered strategy plugin: '{}' ({})", name, strategy_cls.__name__)

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a strategy by name."""
        key = name.lower().strip()
        if key in cls._registry:
            del cls._registry[key]
            cls._metadata.pop(key, None)
            logger.info("Unregistered strategy plugin: '{}'", name)
            return True
        return False

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List registered strategy names."""
        return list(cls._registry.keys())

    @classmethod
    def get_metadata(cls, name: str) -> Optional[StrategyMetadata]:
        """Get strategy metadata by name."""
        return cls._metadata.get(name.lower().strip())

    @classmethod
    def load(cls, name: str) -> Type[Strategy]:
        """Retrieve a strategy class by name."""
        key = name.lower().strip()
        if key not in cls._registry:
            cls.discover_strategies()
            if key not in cls._registry:
                raise KeyError(
                    f"Strategy '{name}' not found in registry. Registered: {cls.list_strategies()}"
                )
        return cls._registry[key]

    @classmethod
    def instantiate(cls, name: str, **kwargs: Any) -> Strategy:
        """Instantiate a strategy by name with keyword arguments."""
        strategy_cls = cls.load(name)
        return strategy_cls(**kwargs)

    @classmethod
    def discover_strategies(cls, package_path: Optional[Path] = None) -> List[str]:
        """Dynamically discover and register all Strategy subclasses in app/strategies."""
        discovered: List[str] = []
        strategies_dir = package_path or (Path(__file__).parent)

        if not strategies_dir.exists():
            return discovered

        for module_info in pkgutil.iter_modules([str(strategies_dir)]):
            mod_name = module_info.name
            if mod_name.startswith("_") or mod_name in ("base", "registry", "engine"):
                continue

            full_mod_name = f"app.strategies.{mod_name}"
            try:
                mod = importlib.import_module(full_mod_name)
                for attr_name, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, Strategy) and obj is not Strategy:
                        reg_name = getattr(obj, "name", attr_name.replace("Strategy", "").lower())
                        if reg_name not in cls._registry:
                            meta = getattr(
                                obj,
                                "metadata",
                                StrategyMetadata(
                                    name=reg_name,
                                    description=obj.__doc__ or f"{reg_name} strategy",
                                ),
                            )
                            cls.register(reg_name, obj, meta)
                            discovered.append(reg_name)
            except Exception as err:
                logger.warning("Failed to load strategy module '{}': {}", full_mod_name, str(err))

        return discovered
