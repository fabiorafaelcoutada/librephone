"""Tests for tlv_decoder.py — WCN6750 TLV descriptor parser."""

import struct
from pathlib import Path

import pytest

from tools.librephone.tlv_decoder import TlvDecoder, TlvTag


def _tlv_16(tag: int, length: int) -> bytes:
    """Encode a tlv_16 header: cflg=0(bit0), tag(1-5), len(6-9), reserved(10-15)."""
    return struct.pack("<H", (tag << 1) | (length << 6))


def _tlv_32(tag: int, length: int) -> bytes:
    """Encode a tlv_32 header: cflg=0(bit0), tag(1-9), len(10-25), reserved(26-31)."""
    return struct.pack("<I", (tag << 1) | (length << 10))


def _tlv_42(tag: int, length: int, usrid: int = 0) -> bytes:
    """Encode a tlv_42 header: compression=1(bit0), tag(1-9), len(10-25), usrid(26-31)."""
    return struct.pack("<Q", (1 << 0) | (tag << 1) | (length << 10) | (usrid << 26))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def decoder() -> TlvDecoder:
    """Create a decoder using the real tlv_tag_def.h file."""
    tag_file = (
        Path(__file__).parent.parent.parent
        / "sm7635-modules" / "qcom" / "opensource" / "wlan"
        / "fw-api" / "hw" / "qca6750" / "v1" / "tlv_tag_def.h"
    )
    return TlvDecoder(tag_file=tag_file)


# ---------------------------------------------------------------------------
# Basic tag loading
# ---------------------------------------------------------------------------

class TestTagLoading:
    def test_loaded_tags(self, decoder):
        """Should load hundreds of tags from the real tlv_tag_def.h."""
        assert decoder.count > 300
        assert decoder.count <= 500

    def test_categories(self, decoder):
        """Should have multiple categories."""
        assert len(decoder.categories) > 10

    def test_specific_tags_exist(self, decoder):
        """Known tags should be present."""
        assert decoder.lookup(0) is not None    # WIFIMACTX_CBF_START
        assert decoder.lookup(137) is not None  # WIFITX_DATA
        assert decoder.lookup(211) is not None  # WIFIRX_ATTENTION

    def test_tag_values(self, decoder):
        """Tags should have correct IDs and names."""
        tag0 = decoder.lookup(0)
        assert tag0.tag_id == 0
        assert "CBF_START" in tag0.name

        tag_dummy = decoder.lookup(109)
        assert tag_dummy.tag_id == 109
        assert tag_dummy.name == "WIFIDUMMY"

    def test_unknown_tag_returns_none(self, decoder):
        """Looking up a non-existent tag should return None."""
        assert decoder.lookup(9999) is None


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

class TestLookup:
    def test_lookup_by_numeric_id(self, decoder):
        """Lookup by decimal ID should work."""
        tag = decoder.lookup(137)
        assert tag is not None
        assert tag.name == "WIFITX_DATA"

    def test_lookup_by_hex(self, decoder):
        """Implementation detail: int('0x89', 0) = 137."""
        tag = decoder.lookup(int("0x89", 0))
        assert tag is not None
        assert tag.tag_id == 137

    def test_lookup_by_name(self, decoder):
        """Lookup by exact name."""
        tag = decoder.lookup_by_name("WIFIDUMMY")
        assert tag is not None
        assert tag.tag_id == 109

    def test_lookup_by_name_case_insensitive(self, decoder):
        """Lookup by name should be case-insensitive."""
        tag = decoder.lookup_by_name("wifidummy")
        assert tag is not None
        assert tag.tag_id == 109

    def test_lookup_by_name_nonexistent(self, decoder):
        """Non-existent name returns None."""
        assert decoder.lookup_by_name("NONEXISTENT_TAG") is None


# ---------------------------------------------------------------------------
# Category extraction
# ---------------------------------------------------------------------------

class TestCategoryExtraction:
    def test_wifimactx_category(self):
        """WIFIMACTX_CBF_START → WIFIMACTX."""
        cat = TlvDecoder._extract_category("WIFIMACTX_CBF_START_E")
        assert cat == "WIFIMACTX"

    def test_wifiphyrx_category(self):
        """WIFIPHYRX_DATA_E → WIFIPHYRX."""
        cat = TlvDecoder._extract_category("WIFIPHYRX_DATA_E")
        assert cat == "WIFIPHYRX"

    def test_wifitqm_category(self):
        """WIFITQM_GEN_MPDUS_E → WIFITQM."""
        cat = TlvDecoder._extract_category("WIFITQM_GEN_MPDUS_E")
        assert cat == "WIFITQM"

    def test_wifitx_category(self):
        """WIFITX_DATA_E → WIFITX."""
        cat = TlvDecoder._extract_category("WIFITX_DATA_E")
        assert cat == "WIFITX"

    def test_wifirx_category(self):
        """WIFIRX_ATTENTION_E → WIFIRX."""
        cat = TlvDecoder._extract_category("WIFIRX_ATTENTION_E")
        assert cat == "WIFIRX"

    def test_wifiwbm_category(self):
        """WIFIWBM_BUFFER_RING_E → WIFIWBM."""
        cat = TlvDecoder._extract_category("WIFIWBM_BUFFER_RING_E")
        assert cat == "WIFIWBM"

    def test_wifireo_category(self):
        """WIFIREO_UPDATE_RX_REO_QUEUE_STATUS_E → WIFIREO."""
        cat = TlvDecoder._extract_category("WIFIREO_UPDATE_RX_REO_QUEUE_STATUS_E")
        assert cat == "WIFIREO"

    def test_wifisch_category(self):
        """WIFISCHEDULER_CMD_E → WIFISCHEDULER."""
        cat = TlvDecoder._extract_category("WIFISCHEDULER_CMD_E")
        assert cat == "WIFISCHEDULER"

    def test_wifiexample_category(self):
        """WIFIEXAMPLE_TLV_16_E → WIFIEXAMPLE."""
        cat = TlvDecoder._extract_category("WIFIEXAMPLE_TLV_16_E")
        assert cat == "WIFIEXAMPLE"

    def test_wifitxpcu_category(self):
        """WIFITXPCU_BUFFER_STATUS_E → WIFITXPCU."""
        cat = TlvDecoder._extract_category("WIFITXPCU_BUFFER_STATUS_E")
        assert cat == "WIFITXPCU"


# ---------------------------------------------------------------------------
# TLV header decoding
# ---------------------------------------------------------------------------

class TestHeaderDecoding:
    def test_header_16(self, decoder):
        """Decode a 16-bit TLV header."""
        header = _tlv_16(tag=5, length=8)
        result = decoder.decode_header(header, fmt="tlv_16")
        assert result is not None
        assert result["tag_id"] == 5
        assert result["length"] == 8
        assert result["format"] == "tlv_16"
        assert result["header_size"] == 2

    def test_header_32(self, decoder):
        """Decode a 32-bit TLV header (WIFITX_DATA)."""
        header = _tlv_32(tag=137, length=64)
        result = decoder.decode_header(header, fmt="tlv_32")
        assert result is not None
        assert result["tag_id"] == 137  # WIFITX_DATA
        assert result["length"] == 64
        assert result["format"] == "tlv_32"
        assert result["header_size"] == 4

    def test_header_42(self, decoder):
        """Decode a 42-bit (64-bit packed) TLV header."""
        header = _tlv_42(tag=137, length=1024, usrid=5)
        result = decoder.decode_header(header, fmt="tlv_42")
        assert result is not None
        assert result["format"] == "tlv_42"
        assert result["tag_id"] == 137
        assert result["length"] == 1024
        assert result["user_id"] == 5
        assert result["has_user_id"] is True
        assert result["header_size"] == 8

    def test_auto_detect_32(self, decoder):
        """Auto-detect should find tlv_32 correctly (WIFITX_DATA)."""
        header = _tlv_32(tag=137, length=64)
        result = decoder.decode_header(header)
        assert result is not None
        assert result["tag_id"] == 137
        assert result["format"] == "tlv_32"


class TestStreamDecoding:
    def test_single_tlv_16(self, decoder):
        """Decode a single TLV 16-bit header in stream."""
        data = _tlv_16(tag=5, length=8)
        items = decoder.decode_stream(data, default_fmt="tlv_16")
        assert len(items) == 1
        assert items[0]["tag_id"] == 5
        assert items[0]["length"] == 8

    def test_multiple_tlvs(self, decoder):
        """Decode a stream of multiple TLV headers with payloads."""
        # TLV stream: hdr1(tag=5,len=4) + 4 payload bytes + hdr2(tag=6,len=0)
        data = _tlv_16(tag=5, length=4) + b"\x00" * 4 + _tlv_16(tag=6, length=0)
        items = decoder.decode_stream(data, default_fmt="tlv_16")
        assert len(items) == 2
        assert items[0]["tag_id"] == 5
        assert items[0]["length"] == 4
        assert items[1]["tag_id"] == 6
        assert items[1]["length"] == 0

    def test_stream_with_payload(self, decoder):
        """Decode TLV with payload (skip past payload to next)."""
        h1 = _tlv_16(tag=5, length=8)    # skip 8 bytes
        payload = b"\x00" * 8
        h2 = _tlv_16(tag=9, length=3)
        items = decoder.decode_stream(h1 + payload + h2, default_fmt="tlv_16")
        assert len(items) == 2
        assert items[0]["tag_id"] == 5
        assert items[0]["length"] == 8
        assert items[1]["tag_id"] == 9
        assert items[1]["length"] == 3

    def test_empty_stream(self, decoder):
        """Empty data returns empty stream."""
        assert decoder.decode_stream(b"") == []

    def test_short_incomplete_header(self, decoder):
        """Incomplete header returns empty (need at least 2 bytes)."""
        assert decoder.decode_stream(b"\x00") == []

    def test_hex_decode(self, decoder):
        """Verify --decode-hex with WIFIDUMMY (tag=109)."""
        # WIFIDUMMY (tag 109) in 32-bit format: cflg=0, tag=109, len=0
        header = _tlv_32(tag=109, length=0)
        items = decoder.decode_stream(header)
        assert len(items) == 1
        assert items[0]["tag_name"] == "WIFIDUMMY"


class TestEdgeCases:
    def test_decoder_with_no_file(self, monkeypatch):
        """Decoder created with no file should have no tags."""
        monkeypatch.setattr(TlvDecoder, "_auto_locate_and_parse", lambda self: None)
        d = TlvDecoder()
        assert d.count == 0

    def test_decode_header_truncated(self, decoder):
        """Less than 2 bytes returns None."""
        assert decoder.decode_header(b"") is None
        assert decoder.decode_header(b"\x00") is None

    def test_decode_header_unknown_format(self, decoder):
        """Non-matching header returns None in auto mode."""
        data = bytes([0xFF, 0xFF, 0xFF, 0xFF])
        # 0xFFFFFFFF: 32-bit cflg=bit0=1 → not tlv_32
        # need 8 bytes for tlv_42 check
        # 16-bit cflg=bit0 of first word = (0xFFFF>>0)&1=1 → not tlv_16
        result = decoder.decode_header(data)
        assert result is None

    def test_auto_locate_missing_file(self, monkeypatch):
        """Auto-locate should not crash when file is missing."""
        monkeypatch.setattr(TlvDecoder, "_auto_locate_and_parse", lambda self: None)
        d = TlvDecoder()
        assert d.count == 0

    def test_lookup_by_partial_name_via_cli(self, decoder):
        """Partial name match — lookup_by_name does exact match."""
        assert decoder.lookup_by_name("TX_DATA") is None
        assert decoder.lookup(137).name == "WIFITX_DATA"
