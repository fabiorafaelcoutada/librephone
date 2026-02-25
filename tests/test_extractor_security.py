"""Tests for security vulnerabilities in extractor.py."""

import os
import pytest
from pathlib import Path
from librephone.extractor import Extractor

@pytest.fixture
def test_env(tmp_path):
    """Setup a temporary test environment with a fake directory structure."""
    # Setup directories
    base_dir = tmp_path / "test_env"
    base_dir.mkdir()

    # Create device directory: .../vendor/model
    device_dir = base_dir / "vendor" / "model"
    device_dir.mkdir(parents=True)

    # Create fake img
    (device_dir / "system.img").write_text("fake img")

    # Fake lineage dir structure
    lineage_dir = base_dir / "lineage"
    lineage_dir.mkdir()

    prop_dir = lineage_dir / "device" / "vendor" / "model"
    prop_dir.mkdir(parents=True)

    # Return paths as strings for Extractor compatibility
    return {
        "base": str(base_dir),
        "device": str(device_dir),
        "lineage": str(lineage_dir),
        "prop": str(prop_dir),
    }

def test_malicious_dependencies_no_execution(test_env, monkeypatch):
    """Test that malicious code in lineage.dependencies is NOT executed."""
    prop_dir = test_env["prop"]

    # Create malicious lineage.dependencies
    # This payload would execute touch pwned_test if eval() was used
    malicious_code = "[{'target_path': 'foo', 'side_effect': __import__('os').system('touch pwned_test')}]"

    deps_file = os.path.join(prop_dir, "lineage.dependencies")
    with open(deps_file, "w") as f:
        f.write(malicious_code)

    extractor = Extractor()

    # Mock methods to avoid side effects
    monkeypatch.setattr(extractor, "mount", lambda x: True)
    monkeypatch.setattr(extractor, "unmount", lambda x: True)
    monkeypatch.setattr(extractor, "parse_proprietary_file", lambda x: {})
    # Mock get_devpath to return 'model'
    monkeypatch.setattr(extractor, "get_devpath", lambda x: "model")

    # Ensure pwned_test doesn't exist
    if os.path.exists("pwned_test"):
        os.remove("pwned_test")

    # The clone method catches Exception, so it shouldn't raise,
    # but we care about the side effect.
    extractor.clone(lineage=test_env["lineage"], indir=test_env["device"], outdir="out")

    # Check if pwned_test exists in CWD (where os.system would create it)
    assert not os.path.exists("pwned_test"), "Arbitrary code execution occurred!"

def test_python_literal_dependencies(test_env, monkeypatch):
    """Test that Python literals (like single quotes) in lineage.dependencies are parsed correctly."""
    prop_dir = test_env["prop"]
    lineage_dir = test_env["lineage"]

    # Python literal using single quotes (not valid JSON)
    literal_data = "[{'target_path': 'device/vendor/common'}]"

    deps_file = os.path.join(prop_dir, "lineage.dependencies")
    with open(deps_file, "w") as f:
        f.write(literal_data)

    # Create the target proprietary file so we can verify it was found
    # Logic: .../device/vendor/common/model/proprietary-files.txt
    common_dir = os.path.join(lineage_dir, "device", "vendor", "common", "model")
    os.makedirs(common_dir, exist_ok=True)
    target_file = os.path.join(common_dir, "proprietary-files.txt")
    with open(target_file, "w") as f:
        f.write("# found me")

    extractor = Extractor()

    monkeypatch.setattr(extractor, "mount", lambda x: True)
    monkeypatch.setattr(extractor, "unmount", lambda x: True)
    monkeypatch.setattr(extractor, "get_devpath", lambda x: "model")

    found_files = []
    def mock_parse(filespec):
        found_files.append(filespec)
        return {}
    monkeypatch.setattr(extractor, "parse_proprietary_file", mock_parse)

    extractor.clone(lineage=test_env["lineage"], indir=test_env["device"], outdir="out")

    # Verify that the correct proprietary file was processed
    assert any("common/model/proprietary-files.txt" in f for f in found_files), "Did not process python literal dependency correctly"
