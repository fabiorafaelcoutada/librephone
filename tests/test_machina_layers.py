"""Tests for Machina base abstractions."""
import unittest

from librephone.machina.conf.config import Config
from librephone.machina.core.context import Context
from librephone.machina.core.engine import Engine
from librephone.machina.targets.arm import ArmTarget
from librephone.machina.layers.kernel import LinuxKernel
from librephone.machina.core.task import TaskStatus

class TestBaseAbstractions(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.target = ArmTarget(name="test-arm", arch="arm64")
        self.context = Context(self.config, target=self.target)
        self.engine = Engine(self.context)

    def test_kernel_build_flow(self):
        """Verify that a component can generate tasks and the engine can execute them."""
        kernel = LinuxKernel(name="linux", source_url="https://kernel.org/linux.git")
        tasks = kernel.get_tasks(self.context)

        for t in tasks:
            self.engine.add_task(t)

        # Verify dependency resolution
        resolved = self.engine.resolve_dependencies()
        names = [t.name for t in resolved]
        self.assertEqual(names, ["linux_fetch", "linux_config", "linux_build"])

        # Verify execution
        success = self.engine.run()
        self.assertTrue(success)

        # Check if tasks were marked as success
        self.assertEqual(self.engine.tasks["linux_build"].status, TaskStatus.SUCCESS)

if __name__ == "__main__":
    unittest.main()
