"""Tests for security vulnerabilities in the Extractor class."""

import json
from unittest.mock import patch

from librephone.extractor import Extractor


def test_clone_dependency_security(tmp_path, capsys):
    """Verify that lineage.dependencies is parsed as JSON and not evaluated as code.

    This prevents Arbitrary Code Execution if the file contains malicious Python code.
    """
    root = tmp_path

    # Setup directory structure similar to what Extractor.clone expects
    indir = root / "vendor_name" / "device_name"
    indir.mkdir(parents=True)

    # Create a dummy image file so glob works and logic proceeds
    (indir / "boot.img").touch()

    lineage = root / "lineage"
    lineage.mkdir()

    # Logic for propdir in Extractor.clone:
    # devdir = f"{tmp[-2].lower()}/{build}"
    # We will mock get_devpath to return "device_name"

    devdir = "vendor_name/device_name"
    propdir = lineage / "device" / devdir
    propdir.mkdir(parents=True)

    deps_file = propdir / "lineage.dependencies"

    # Malicious content that prints "VULNERABLE" if executed
    # Using 'or []' to satisfy iteration if it were evaluated,
    # but print returns None so it would crash anyway after printing.
    payload = "print('VULNERABLE') or []"
    with open(deps_file, "w") as f:
        f.write(payload)

    extractor = Extractor()

    # Mock external calls and lengthy operations
    with patch("subprocess.run"), patch("shutil.copy"), patch("shutil.copy2"), patch.object(
        Extractor, "mount", return_value=True
    ), patch.object(Extractor, "unmount", return_value=True), patch.object(
        Extractor, "clone_generic", return_value=True
    ), patch.object(
        Extractor, "get_devpath", return_value="device_name"
    ):
        # Run clone
        # It should fail to parse JSON and catch the exception, but NOT execute the code
        extractor.clone(str(lineage), str(indir), str(root / "out"))

    captured = capsys.readouterr()
    assert "VULNERABLE" not in captured.out


def test_clone_dependency_valid_json(tmp_path):
    """Verify that valid JSON in lineage.dependencies is parsed correctly."""
    root = tmp_path

    indir = root / "vendor_name" / "device_name"
    indir.mkdir(parents=True)
    (indir / "boot.img").touch()

    lineage = root / "lineage"
    lineage.mkdir()

    devdir = "vendor_name/device_name"
    propdir = lineage / "device" / devdir
    propdir.mkdir(parents=True)

    deps_file = propdir / "lineage.dependencies"

    # Valid content
    payload = json.dumps([{"target_path": "some/other/path"}])
    with open(deps_file, "w") as f:
        f.write(payload)

    extractor = Extractor()

    # We mock glob to spy on calls
    with patch("subprocess.run"), patch("shutil.copy"), patch("shutil.copy2"), patch.object(
        Extractor, "mount", return_value=True
    ), patch.object(Extractor, "unmount", return_value=True), patch.object(
        Extractor, "clone_generic", return_value=True
    ), patch.object(
        Extractor, "get_devpath", return_value="device_name"
    ), patch(
        "glob.glob", side_effect=lambda x: []
    ) as mock_glob:
        extractor.clone(str(lineage), str(indir), str(root / "out"))

        # Verify glob was called with expected path derived from JSON
        # logic: subprops = f"{os.path.dirname(propdir)}/{os.path.basename(depdir['target_path'])}/{os.path.basename(devdir)}"
        # propdir = .../lineage/device/vendor_name/device_name
        # dirname(propdir) = .../lineage/device/vendor_name
        # target_path = "some/other/path" -> basename = "path"
        # devdir = "vendor_name/device_name" -> basename = "device_name"

        # So subprops = .../lineage/device/vendor_name/path/device_name

        # Verify glob was called with this pattern
        calls = [call[0][0] for call in mock_glob.call_args_list]
        found = False
        for c in calls:
            if "path/device_name/proprietary-*.txt" in c:
                found = True
                break
        assert found, "Did not attempt to glob path derived from valid JSON dependency"
