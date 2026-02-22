"""Build context for Machina."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from librephone.machina.conf.config import Config

@dataclass
class Context:
    """Holds the global state of the build execution."""
    config: Config
    target: Any = None  # Will be a Target object
    layers: List[Any] = field(default_factory=list) # Will be Layer objects
    work_dir: str = "/tmp/machina_build"

    # Shared data between tasks
    data: Dict[str, Any] = field(default_factory=dict)
