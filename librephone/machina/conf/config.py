"""Configuration management for Machina."""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

@dataclass
class Config:
    """Holds the build configuration state."""

    # Project metadata
    project_name: str = "Machina Project"
    version: str = "0.1.0"

    # Build directories
    build_dir: str = "build"
    output_dir: str = "output"

    # Target configuration
    target_arch: str = "arm64"
    target_platform: str = "android"

    # Layers/Modules enabled
    layers: List[str] = field(default_factory=list)

    # Arbitrary settings (loaded from static configs)
    settings: Dict[str, Any] = field(default_factory=dict)

    def update(self, new_config: Dict[str, Any]):
        """Update configuration with new values."""
        for key, value in new_config.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.settings[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a setting value."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.settings.get(key, default)
