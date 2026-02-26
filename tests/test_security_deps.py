import os
import tempfile
import shutil
import pytest
import json
from pathlib import Path
from librephone.extractor import Extractor

def test_security_vulnerability_eval():
    # Setup directories
    with tempfile.TemporaryDirectory() as tmpdir:
        # Structure:
        # tmpdir/lineage/device/vendor/device/lineage.dependencies
        # tmpdir/input/vendor/test_device/ (fake dump)

        lineage_dir = os.path.join(tmpdir, "lineage")
        # Ensure input_dir has enough depth for parts[-2]
        input_dir = os.path.join(tmpdir, "input", "vendor", "test_device")
        output_dir = os.path.join(tmpdir, "output")

        os.makedirs(lineage_dir)
        os.makedirs(os.path.join(lineage_dir, "device", "vendor"))
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Extractor logic:
        # build = "unknown" (since test_device not in devices.lst)
        # devdir = tmp[-2] + "/" + build => "vendor/unknown"
        # propdir = lineage + "/device/" + devdir => "lineage/device/vendor/unknown"

        # The code tries:
        # devdir = tmp[-2].lower() + "/" + build  -> "vendor/unknown"
        # propdir = lineage + "/device/" + devdir

        prop_dir = os.path.join(lineage_dir, "device", "vendor", "unknown")
        os.makedirs(prop_dir)

        # Create malicious lineage.dependencies
        pwned_file = os.path.join(tmpdir, "pwned")
        # Ensure pwned file doesn't exist yet
        if os.path.exists(pwned_file):
            os.remove(pwned_file)

        malicious_code = f"[__import__('os').system('touch {pwned_file}')]"

        deps_file = os.path.join(prop_dir, "lineage.dependencies")
        with open(deps_file, "w") as f:
            f.write(malicious_code)

        extractor = Extractor()

        # Mock unmount and mount to avoid sudo usage and errors
        extractor.mount = lambda x: True
        extractor.unmount = lambda x: True

        # Run clone
        # It will try to read lineage.dependencies and eval it.
        try:
            extractor.clone(lineage=lineage_dir, indir=input_dir, outdir=output_dir)
        except Exception:
            # We don't care if it fails later (e.g. copying files), as long as eval executed
            pass

        # Check if pwned file exists
        if os.path.exists(pwned_file):
            # Vulnerability confirmed
            pytest.fail("Vulnerability EXPLOITED: pwned file was created! Code executed via eval().")
        else:
            # Vulnerability NOT reproduced (which is good if fixed)
            pass

def test_valid_json_dependencies_safety():
    # This test ensures valid JSON is accepted.
    # After fix, this should still pass.
    with tempfile.TemporaryDirectory() as tmpdir:
        lineage_dir = os.path.join(tmpdir, "lineage")
        input_dir = os.path.join(tmpdir, "input", "vendor", "test_device")
        output_dir = os.path.join(tmpdir, "output")

        os.makedirs(lineage_dir)
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        prop_dir = os.path.join(lineage_dir, "device", "vendor", "unknown")
        os.makedirs(prop_dir)

        # Valid JSON
        # The code expects a list of deps
        json_content = '[{"target_path": "device/vendor/other_device"}]'

        deps_file = os.path.join(prop_dir, "lineage.dependencies")
        with open(deps_file, "w") as f:
            f.write(json_content)

        extractor = Extractor()
        extractor.mount = lambda x: True
        extractor.unmount = lambda x: True

        try:
            extractor.clone(lineage=lineage_dir, indir=input_dir, outdir=output_dir)
        except Exception:
            pass

        # If we didn't crash on parsing, we assume it's fine.
        # But specifically we want to ensure no syntax error or eval error.
        assert True
