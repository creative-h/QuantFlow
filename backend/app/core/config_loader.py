"""Configuration loader for YAML strategy configs and environment settings."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from loguru import logger


def load_strategy_yaml(strategy_name: str, config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load YAML configuration for a specified strategy."""
    base_dir = config_dir or (Path(__file__).parent.parent.parent / "config" / "strategies")
    yaml_file = base_dir / f"{strategy_name.lower()}.yaml"

    if not yaml_file.exists():
        logger.warning("Strategy YAML config file not found: {}", yaml_file)
        return {}

    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            logger.info("Loaded strategy config from {}", yaml_file.name)
            return data
    except Exception as err:
        logger.error("Failed to parse YAML file {}: {}", yaml_file, str(err))
        return {}
