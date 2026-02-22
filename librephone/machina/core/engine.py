"""Core execution engine for Machina."""
import logging
from typing import Dict, List, Set

from librephone.machina.core.context import Context
from librephone.machina.core.task import Task, TaskStatus

log = logging.getLogger(__name__)

class Engine:
    """Manages task execution and dependencies."""

    def __init__(self, context: Context):
        self.context = context
        self.tasks: Dict[str, Task] = {}

    def add_task(self, task: Task):
        """Add a task to the engine."""
        if task.name in self.tasks:
            log.warning(f"Task {task.name} already exists. Overwriting.")
        self.tasks[task.name] = task

    def resolve_dependencies(self) -> List[Task]:
        """Topologically sort tasks based on dependencies."""
        sorted_tasks = []
        visited = set()
        temp_visited = set()

        def visit(task_name):
            if task_name in temp_visited:
                raise ValueError(f"Circular dependency detected: {task_name}")
            if task_name in visited:
                return
            if task_name not in self.tasks:
                raise ValueError(f"Task {task_name} not found (dependency of another task)")

            temp_visited.add(task_name)

            for dep_name in self.tasks[task_name].dependencies:
                visit(dep_name)

            temp_visited.remove(task_name)
            visited.add(task_name)
            sorted_tasks.append(self.tasks[task_name])

        for task_name in self.tasks:
            if task_name not in visited:
                visit(task_name)

        return sorted_tasks

    def run(self) -> bool:
        """Execute all tasks in dependency order."""
        try:
            execution_order = self.resolve_dependencies()
        except ValueError as e:
            log.error(f"Dependency resolution failed: {e}")
            return False

        log.info(f"Execution plan: {[t.name for t in execution_order]}")

        for task in execution_order:
            if not task.run(self.context):
                log.error(f"Build failed at task: {task.name}")
                return False

        log.info("Build completed successfully.")
        return True
