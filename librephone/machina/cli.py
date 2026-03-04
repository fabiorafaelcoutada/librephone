"""Command Line Interface for Machina."""
import argparse
import logging
import sys
from pathlib import Path

from librephone.machina.conf.config import Config
from librephone.machina.conf.loader import ConfigLoader
from librephone.machina.core.context import Context
from librephone.machina.core.engine import Engine
from librephone.machina.layers.kernel import LinuxKernel
from librephone.machina.targets.arm import AndroidDevice, ArmTarget

log = logging.getLogger(__name__)

def setup_logging(verbose: bool):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

def main():
    """Main entry point for Machina."""
    parser = argparse.ArgumentParser(description="Machina Build System")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--config", help="Configuration file (YAML/JSON/Python)")
    parser.add_argument("target", help="Target device (e.g., generic-arm, pixel6)")

    args = parser.parse_args()
    setup_logging(args.verbose)

    log.info(f"Starting Machina build for target: {args.target}")

    # 1. Load Configuration
    config = Config()
    loader = ConfigLoader(config)
    if args.config:
        loader.load_from_file(args.config)

    # 2. Resolve Target (Mock implementation for now)
    target = None
    if args.target == "generic-arm":
        target = ArmTarget(name="Generic ARM")
    elif args.target == "android":
        target = AndroidDevice(name="Android Device")
    else:
        log.error(f"Unknown target: {args.target}")
        sys.exit(1)

    log.info(f"Target Resolved: {target.name} (Arch: {target.arch})")

    # 3. Initialize Context and Engine
    context = Context(config, target=target)
    engine = Engine(context)

    # 4. Add Layers/Components (Mock implementation)
    # In a real scenario, this would come from config or target definition
    kernel = LinuxKernel(name="linux-6.1", source_url="https://kernel.org")

    log.info("Generating build tasks...")
    tasks = kernel.get_tasks(context)
    for task in tasks:
        engine.add_task(task)

    # 5. Execute Build
    log.info("Starting execution...")
    success = engine.run()

    if success:
        log.info("Build SUCCESS!")
        sys.exit(0)
    else:
        log.error("Build FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
