"""Example Machina configuration (Dynamic Python)."""
from librephone.machina.targets.arm import ArmTarget

def configure(config):
    """Configure the build."""
    config.project_name = "My Custom Phone OS"
    config.version = "1.0.0-alpha"

    # We can perform logic here
    if config.target_platform == "android":
        config.layers.append("android-13")
    else:
        config.layers.append("minimal-linux")

    print(f"Configured project: {config.project_name}")
