"""Task definition for Machina."""
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Optional, Set

log = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()

@dataclass
class Task:
    """Represents a unit of work in the build system."""
    name: str
    description: str = ""
    dependencies: Set[str] = field(default_factory=set)
    action: Optional[Callable] = None
    status: TaskStatus = TaskStatus.PENDING

    def run(self, context) -> bool:
        """Execute the task action."""
        if not self.action:
            log.warning(f"Task {self.name} has no action.")
            return True

        log.info(f"Running task: {self.name}")
        try:
            self.status = TaskStatus.RUNNING
            result = self.action(context)
            if result is False:
                self.status = TaskStatus.FAILED
                return False
            self.status = TaskStatus.SUCCESS
            return True
        except Exception as e:
            log.error(f"Task {self.name} failed with exception: {e}")
            self.status = TaskStatus.FAILED
            return False
