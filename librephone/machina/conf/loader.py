"""Configuration loading logic for Machina."""
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

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

        if path.suffix in ['.yaml', '.yml']:
            self._load_yaml(path)
        elif path.suffix == '.json':
            self._load_json(path)
        elif path.suffix == '.py':
            self._load_python(path)
        else:
            log.error(f"Unsupported configuration format: {path.suffix}")

    def _load_yaml(self, path: Path) -> None:
        """Load YAML configuration."""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    self.config.update(data)
        except Exception as e:
            log.error(f"Failed to load YAML config {path}: {e}")

    def _load_json(self, path: Path) -> None:
        """Load JSON configuration."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                if data:
                    self.config.update(data)
        except Exception as e:
            log.error(f"Failed to load JSON config {path}: {e}")

    def _load_python(self, path: Path) -> None:
        """Load Python configuration module."""
        try:
            # Import the python file as a module
            spec = importlib.util.spec_from_file_location("machina_user_config", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["machina_user_config"] = module
            spec.loader.exec_module(module)

            # Look for a 'configure' function or a 'CONFIG' dictionary
            if hasattr(module, 'configure'):
                # Allow the user function to modify the config object directly
                module.configure(self.config)
            elif hasattr(module, 'CONFIG'):
                # Update with the dictionary
                self.config.update(module.CONFIG)
            else:
                log.warning(f"Python config {path} must define 'configure(config)' or 'CONFIG' dict.")

        except Exception as e:
            log.error(f"Failed to load Python config {path}: {e}")
