
import os
import shutil
import tempfile
import pytest
from librephone.device_files import DeviceFiles
from librephone.typedefs import Bintypes

def test_ios_magic_detection():
    df = DeviceFiles()
    # Create temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mach-O 64-bit LE (0xcffaedfe)
        macho_path = os.path.join(tmpdir, "test_macho")
        with open(macho_path, "wb") as f:
            f.write(bytes([0xcf, 0xfa, 0xed, 0xfe]))

        # Verify
        magic_type = df.get_magic(macho_path)
        assert magic_type == Bintypes.MACH_O

        # PNG (should be GRAPHIC)
        png_path = os.path.join(tmpdir, "test.png")
        with open(png_path, "wb") as f:
            f.write(bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]))

        # Verify
        magic_type = df.get_magic(png_path)
        assert magic_type == Bintypes.GRAPHIC

def test_find_files_generic():
    df = DeviceFiles()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a structure: /bin/ls
        bin_dir = os.path.join(tmpdir, "bin")
        os.makedirs(bin_dir)

        # Create a file
        fpath = os.path.join(bin_dir, "ls")
        with open(fpath, "wb") as f:
            f.write(bytes([0x7f, 0x45, 0x4c, 0x46])) # ELF64

        # Run with force_all=True to ensure generic mode picks it up
        files = df.find_files(tmpdir, force_all=True)

        # Check if ELF64 key exists
        assert Bintypes.ELF64.value in files
        # Check if file is in list
        found = False
        for entry in files[Bintypes.ELF64.value]:
            if entry["file"] == "ls":
                found = True
                break
        assert found

def test_ios_nametypes():
    df = DeviceFiles()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file with ios name pattern
        plist_path = os.path.join(tmpdir, "Info.plist")
        with open(plist_path, "w") as f:
            f.write("xml content")

        # Verify detection via name
        # Note: get_magic checks name patterns first
        magic_type = df.get_magic(plist_path)
        # Should be CONFIG (mapped from .plist in NAMETYPES)
        assert magic_type == Bintypes.CONFIG
