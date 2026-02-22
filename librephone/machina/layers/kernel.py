"""Linux Kernel component."""
import logging
from typing import List

from librephone.machina.core.task import Task
from librephone.machina.layers.layer import Component

log = logging.getLogger(__name__)

class LinuxKernel(Component):
    """Linux Kernel builder."""

    def get_tasks(self, context) -> List[Task]:
        tasks = []

        def fetch(ctx):
            log.info(f"Fetching kernel source from {self.source_url}...")
            return True

        def configure(ctx):
            log.info(f"Configuring kernel for {ctx.target.arch}...")
            return True

        def build(ctx):
            toolchain = ctx.target.get_toolchain()
            log.info(f"Building kernel using {toolchain}gcc...")
            return True

        task_fetch = Task(name=f"{self.name}_fetch", action=fetch)
        task_config = Task(name=f"{self.name}_config", action=configure, dependencies={task_fetch.name})
        task_build = Task(name=f"{self.name}_build", action=build, dependencies={task_config.name})

        return [task_fetch, task_config, task_build]
