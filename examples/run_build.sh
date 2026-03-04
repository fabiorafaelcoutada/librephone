#!/bin/bash
# Example script to run a Machina build
# Note: In a real environment, 'machina' would be in the PATH.
# Here we use python -m to run it from the repo root.

export PYTHONPATH=$(pwd)

echo "--- Running build with Default settings ---"
python3 -m librephone.machina.cli generic-arm
echo ""

echo "--- Running build with YAML Config ---"
python3 -m librephone.machina.cli -c examples/machina.yaml generic-arm
echo ""

echo "--- Running build with Python Config ---"
python3 -m librephone.machina.cli -c examples/simple_arm_build.py generic-arm
