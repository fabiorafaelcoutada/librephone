"""Tests for Machina Core Engine."""
import unittest

from librephone.machina.conf.config import Config
from librephone.machina.core.context import Context
from librephone.machina.core.engine import Engine
from librephone.machina.core.task import Task, TaskStatus

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.context = Context(self.config)
        self.engine = Engine(self.context)

    def test_dependency_resolution(self):
        """Test simple dependency chain."""
        task_a = Task(name="A", dependencies={"B"})
        task_b = Task(name="B", dependencies={"C"})
        task_c = Task(name="C")

        self.engine.add_task(task_a)
        self.engine.add_task(task_b)
        self.engine.add_task(task_c)

        sorted_tasks = self.engine.resolve_dependencies()
        names = [t.name for t in sorted_tasks]

        # Should be C -> B -> A
        self.assertEqual(names, ["C", "B", "A"])

    def test_circular_dependency(self):
        """Test circular dependency detection."""
        task_a = Task(name="A", dependencies={"B"})
        task_b = Task(name="B", dependencies={"A"})

        self.engine.add_task(task_a)
        self.engine.add_task(task_b)

        with self.assertRaises(ValueError):
            self.engine.resolve_dependencies()

    def test_task_execution(self):
        """Test task execution success."""
        executed = []
        def action_fn(context):
            executed.append("run")
            return True

        task = Task(name="T", action=action_fn)
        self.engine.add_task(task)

        success = self.engine.run()
        self.assertTrue(success)
        self.assertEqual(executed, ["run"])
        self.assertEqual(task.status, TaskStatus.SUCCESS)

if __name__ == "__main__":
    unittest.main()
