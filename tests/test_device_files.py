from unittest.mock import mock_open, patch

import pytest

from librephone.device_files import DeviceFiles
from librephone.typedefs import Bintypes


class TestDeviceFiles:
    @pytest.fixture
    def device_files(self):
        return DeviceFiles()

    def test_get_magic_avb(self, device_files):
        # AVB magic number: 41 56 42 30 (AVB0)
        avb_magic = b"\x41\x56\x42\x30"
        with patch("builtins.open", mock_open(read_data=avb_magic)):
            # We mock the file read to return AVB0
            # Note: builtins.open is used in get_magic
            assert device_files.get_magic("test.bin") == Bintypes.AVB

    def test_get_magic_unknown(self, device_files):
        # Random bytes
        random_magic = b"\x00\x01\x02\x03"
        with patch("builtins.open", mock_open(read_data=random_magic)):
            assert device_files.get_magic("test.bin") == Bintypes.UNKNOWN

    def test_get_magic_by_filename(self, device_files):
        # Test pattern matching in get_magic
        # "adsp.b01" -> Bintypes.MODEM
        # We need to ensure open() fails or we don't reach it if name matches?
        # Actually get_magic checks name first.

        # But wait, get_magic implementation:
        # for name in nametypes: ... return name["type"]

        assert device_files.get_magic("adsp.b01") == Bintypes.MODEM
        assert device_files.get_magic("modem.img") == Bintypes.CELL_WIFI_GPS_BLUETOOTH

    @patch("os.stat")
    @patch("hashlib.md5")
    @patch("magic.from_file")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_metadata(self, mock_file, mock_magic, mock_md5, mock_stat, device_files):
        # Setup mocks
        mock_stat.return_value.st_size = 1024
        mock_md5.return_value.hexdigest.return_value = "dummy_md5"
        mock_magic.return_value = "ELF 64-bit LSB pie executable, ARM aarch64"

        # Mock get_magic to return something specific if called
        with patch.object(DeviceFiles, "get_magic", return_value=Bintypes.ELF64):
            metadata = device_files.get_metadata("test_file.bin")

        assert metadata["file"] == "test_file.bin"
        assert metadata["size"] == 1024
        assert metadata["md5sum"] == "dummy_md5"
        # assert metadata["type"] == Bintypes.ELF64.value # get_metadata calls get_magic(filespec).value
        # Wait, get_metadata calls self.get_magic(filespec).value

    def test_get_magic_png_works(self, device_files):
        # PNG magic is 8 bytes. Previously buggy, now fixed.
        png_magic = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"
        with patch("builtins.open", mock_open(read_data=png_magic)):
            # Should return GRAPHIC now
            assert device_files.get_magic("test.png") == Bintypes.GRAPHIC
