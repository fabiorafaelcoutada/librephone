"""ARM target definitions."""
from dataclasses import dataclass

from librephone.machina.targets.target import BaseTarget

@dataclass
class ArmTarget(BaseTarget):
    """Generic ARM target."""
    arch: str = "arm64"

    def get_toolchain(self) -> str:
        return "aarch64-linux-gnu-"

@dataclass
class AndroidDevice(ArmTarget):
    """Android-specific ARM device."""
    android_version: str = "13.0"

    def __post_init__(self):
        self.features.append("android")
