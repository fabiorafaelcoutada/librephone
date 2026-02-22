"""Base layer and component definitions."""
from dataclasses import dataclass, field
from typing import List, Optional

from librephone.machina.core.task import Task

@dataclass
class Component:
    """A buildable software component (e.g., Kernel, Bootloader)."""
    name: str
    version: str = "latest"
    source_url: Optional[str] = None

    def get_tasks(self, context) -> List[Task]:
        """Generate tasks required to build this component."""
        return []

@dataclass
class Layer:
    """A collection of components and configuration."""
    name: str
    components: List[Component] = field(default_factory=list)

    def prepare(self, context):
        """Prepare the layer (e.g., set up environment)."""
        pass
