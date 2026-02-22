"""Tests for Machina configuration system."""
import os
import tempfile
import unittest
from pathlib import Path

from librephone.machina.conf.config import Config
from librephone.machina.conf.loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.loader = ConfigLoader(self.config)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_yaml(self):
        filepath = Path(self.temp_dir.name) / "config.yaml"
        with open(filepath, "w") as f:
            f.write("project_name: Test Project\nversion: 1.2.3\n")

        self.loader.load_from_file(filepath)
        self.assertEqual(self.config.project_name, "Test Project")
        self.assertEqual(self.config.version, "1.2.3")

    def test_load_json(self):
        filepath = Path(self.temp_dir.name) / "config.json"
        with open(filepath, "w") as f:
            f.write('{"target_arch": "x86_64", "custom_setting": 42}')

        self.loader.load_from_file(filepath)
        self.assertEqual(self.config.target_arch, "x86_64")
        self.assertEqual(self.config.settings["custom_setting"], 42)

    def test_load_python_dict(self):
        filepath = Path(self.temp_dir.name) / "config_dict.py"
        with open(filepath, "w") as f:
            f.write("CONFIG = {'layers': ['kernel', 'bootloader']}")

        self.loader.load_from_file(filepath)
        self.assertEqual(self.config.layers, ["kernel", "bootloader"])

    def test_load_python_func(self):
        filepath = Path(self.temp_dir.name) / "config_func.py"
        with open(filepath, "w") as f:
            f.write("def configure(config):\n    config.target_platform = 'ios'")

        self.loader.load_from_file(filepath)
        self.assertEqual(self.config.target_platform, "ios")

if __name__ == "__main__":
    unittest.main()
