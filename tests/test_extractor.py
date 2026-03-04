"""Tests for the Extractor class."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure librephone is in path
sys.path.append(os.getcwd())

from librephone.extractor import Extractor

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    base_dir = tmp_path / "test_extractor"
    base_dir.mkdir()

    lineage_dir = base_dir / "Lineage"
    lineage_dir.mkdir()

    vendor = "google"
    device = "panther"
    prop_dir = lineage_dir / "device" / vendor / device
    prop_dir.mkdir(parents=True)

    indir = base_dir / "input" / vendor / device
    indir.mkdir(parents=True)

    outdir = base_dir / "output"

    return {
        "base_dir": base_dir,
        "lineage_dir": lineage_dir,
        "vendor": vendor,
        "device": device,
        "prop_dir": prop_dir,
        "indir": indir,
        "outdir": outdir
    }

def test_clone_json_parsing(temp_dirs):
    """Verify that lineage.dependencies is parsed as JSON."""
    prop_dir = temp_dirs["prop_dir"]
    lineage_dir = temp_dirs["lineage_dir"]
    indir = temp_dirs["indir"]
    outdir = temp_dirs["outdir"]

    # Valid JSON payload
    payload = [
        {
            "target_path": "device/google/gs101",
            "remote": "github"
        }
    ]

    with open(prop_dir / "lineage.dependencies", "w") as f:
        json.dump(payload, f)

    extractor = Extractor()
    extractor.get_devpath = MagicMock(return_value="panther")
    extractor.mount = MagicMock(return_value=True)
    extractor.unmount = MagicMock(return_value=True)
    extractor.clone_generic = MagicMock(return_value=True)

    with patch("librephone.extractor.glob.glob") as mock_glob:
        mock_glob.return_value = []

        try:
            extractor.clone(str(lineage_dir), indir=str(indir), outdir=str(outdir))
        except Exception:
            pass

        # Verify that glob was called with path constructed from JSON
        # Expected: .../device/google/gs101/panther/proprietary-*.txt
        # Check if any call matches
        found = False
        for call in mock_glob.call_args_list:
            args, _ = call
            if "gs101/panther" in str(args[0]):
                found = True
                break

        assert found, "extractor.clone did not parse JSON correctly to construct path"

def test_clone_malicious_parsing(temp_dirs):
    """Verify that malicious payload in lineage.dependencies is not executed."""
    prop_dir = temp_dirs["prop_dir"]
    lineage_dir = temp_dirs["lineage_dir"]
    indir = temp_dirs["indir"]
    outdir = temp_dirs["outdir"]

    # Malicious payload that is valid python but invalid JSON
    malicious_code = "__import__('os').system('touch /tmp/pwned_test')"
    payload = f"[{malicious_code}]"

    pwned_file = Path("/tmp/pwned_test")
    if pwned_file.exists():
        pwned_file.unlink()

    with open(prop_dir / "lineage.dependencies", "w") as f:
        f.write(payload)

    extractor = Extractor()
    extractor.get_devpath = MagicMock(return_value="panther")
    extractor.mount = MagicMock(return_value=True)
    extractor.unmount = MagicMock(return_value=True)
    extractor.clone_generic = MagicMock(return_value=True)

    # It should raise JSONDecodeError but likely caught by generic except
    try:
        extractor.clone(str(lineage_dir), indir=str(indir), outdir=str(outdir))
    except Exception:
        pass

    assert not pwned_file.exists(), "Malicious code was executed!"
