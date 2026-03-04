"""Base target definition."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class BaseTarget:
    """Abstract base class for a hardware target."""
    name: str
    arch: str = "unknown"
    vendor: str = "unknown"
    model: str = "unknown"

    # Platform specific configuration
    features: List[str] = field(default_factory=list)
    extra_flags: Dict[str, str] = field(default_factory=dict)

    def get_toolchain(self) -> str:
        """Return the toolchain prefix for this target."""
        return ""
