"""Configuration loading logic for Machina."""
import importlib.util
import json
import logging
import sys
from pathlib import Path

import yaml

from librephone.machina.conf.config import Config

log = logging.getLogger(__name__)

class ConfigLoader:
    """Loads configuration from various sources (YAML, JSON, Python)."""

    def __init__(self, config_obj: Config = None):
        self.config = config_obj or Config()

    def load_from_file(self, filepath: str) -> None:
        """Load configuration from a file."""
        path = Path(filepath)
        if not path.exists():
            log.warning(f"Configuration file not found: {filepath}")
            return

        if path.suffix in [".yaml", ".yml"]:
            self._load_yaml(path)
        elif path.suffix == ".json":
            self._load_json(path)
        else:
            log.error(f"Unsupported configuration format: {path.suffix}")

    def _load_yaml(self, path: Path) -> None:
        """Load YAML configuration."""
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                if data:
                    self.config.update(data)
        except Exception as e:
            log.error(f"Failed to load YAML config {path}: {e}")

    def _load_json(self, path: Path) -> None:
        """Load JSON configuration."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
                if data:
                    self.config.update(data)
        except Exception as e:
            log.error(f"Failed to load JSON config {path}: {e}")
