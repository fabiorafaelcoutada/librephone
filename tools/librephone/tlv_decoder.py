"""TLV decoder for WCN6750 hardware descriptors.

Parses the fw-api/hw/qca6750/v1/tlv_tag_def.h definitions and provides
a lookup table for hardware-level TLV (Type-Length-Value) descriptors.

TLV formats (from tlv_hdr.h):

  tlv_16_hdr  (2 bytes):  tag[4:0]=5bits,  len[3:0]=4bits,  cflg[0]
  tlv_32_hdr  (4 bytes):  tag[8:0]=9bits,  len[15:0]=16bits, cflg[0]
  tlv_usr_16  (2 bytes):  tlv_16 + userid[5:0]=6bits
  tlv_usr_32  (4 bytes):  tlv_32 + userid[5:0]=6bits
  tlv_42_hdr  (8 bytes packed): tag=9bits, len=16bits, compression[0]

Usage:
  python -m tools.librephone.tlv_decoder --parse <path/to/tlv_tag_def.h>
  python -m tools.librephone.tlv_decoder --lookup 0x89
  python -m tools.librephone.tlv_decoder --dump-categories
"""

import re
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Default TLV header sizes
TLV_16_HDR_SIZE = 2
TLV_32_HDR_SIZE = 4
TLV_42_HDR_SIZE = 8

# TLV header type widths (bits)
TLV_HEADER_TYPES = {
    16: {"tag_bits": 5, "len_bits": 4, "hdr_size": 2},
    32: {"tag_bits": 9, "len_bits": 16, "hdr_size": 4},
    42: {"tag_bits": 9, "len_bits": 16, "hdr_size": 8},
}


@dataclass
class TlvTag:
    """A single TLV tag definition."""
    tag_id: int
    name: str
    category: str  # e.g., WIFIMACTX, WIFIPHYRX, WIFITQM


class TlvDecoder:
    """Decode WCN6750 TLV descriptors from fw-api tag definitions."""

    TAG_PATTERN = re.compile(
        r"^\s*(WIFI[A-Z_]+)_E\s*=\s*(\d+)\s+/\*\s*(0x[0-9a-fA-F]+)\s*\*/\s*,"
    )
    FILENAME_GUESSED = "tlv_tag_def.h"

    def __init__(self, tag_file: Optional[str | Path] = None):
        self.tags: dict[int, TlvTag] = {}
        self.categories: dict[str, list[TlvTag]] = defaultdict(list)
        if tag_file:
            self._parse_tags(Path(tag_file))
        else:
            self._auto_locate_and_parse()

    def _auto_locate_and_parse(self) -> None:
        """Try to locate tlv_tag_def.h relative to the project root."""
        candidates = [
            Path.cwd() / "sm7635-modules" / "qcom" / "opensource" /
                "wlan" / "fw-api" / "hw" / "qca6750" / "v1" / self.FILENAME_GUESSED,
            Path(__file__).parent.parent.parent / "sm7635-modules" / "qcom" /
                "opensource" / "wlan" / "fw-api" / "hw" / "qca6750" / "v1" /
                self.FILENAME_GUESSED,
        ]
        for path in candidates:
            if path.exists():
                self._parse_tags(path)
                return
        print(f"[tlv_decoder] Could not auto-locate {self.FILENAME_GUESSED}", file=sys.stderr)

    def _parse_tags(self, path: Path) -> None:
        """Parse tlv_tag_def.h and populate tag tables."""
        content = path.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            m = self.TAG_PATTERN.match(line)
            if not m:
                continue
            name = m.group(1)
            tag_id = int(m.group(2))
            # group(3) is hex comment like 0x89

            category = self._extract_category(name)
            tag = TlvTag(tag_id=tag_id, name=name, category=category)
            self.tags[tag_id] = tag
            self.categories[category].append(tag)

    @staticmethod
    def _extract_category(name: str) -> str:
        """Extract subsystem category from a TLV tag name.

        WIFIMACTX_CBF_START_E  → WIFIMACTX
        WIFIPHYRX_DATA_E       → WIFIPHYRX
        WIFITQM_GEN_MPDUS_E    → WIFITQM
        WIFIRX_MPDU_END_E      → WIFIRX
        WIFIEXAMPLE_*          → WIFIEXAMPLE (debug/demo)
        WIFIREO_*              → WIFIREO
        WIFIWBM_*              → WIFIWBM
        WIFIUNIFORM_*          → WIFIUNIFORM
        WIFIOLE_*              → WIFIOLE
        WIFICOEX_*             → WIFICOEX
        WIFIPCU_*              → WIFIPCU
        WIFISCH_* / WIFISCHEDULER_* → WIFISCH
        WIFIPDG_*              → WIFIPDG
        WIFIDATA_*             → WIFIDATA
        WIFIOFDMA_*            → WIFIOFDMA
        WIFIRXPCU_* / WIFITXPCU_* → WIFIxPCU
        WIFIRXPCT_*            → WIFIRXPT
        WIFIMPDU_*             → WIFIRX (generic RX)
        WIFINA_*               → WIFINA
        WIFIMIMO_*             → WIFIMIMO
        WIFIPPDU_* / WIFIPROT_* → WIFIRX (PPDU/protocol)
        WIFIRX_PHY_*           → WIFIRXPHY
        WIFIADDR_*             → WIFIADDR
        WIFIRESPONSE_*         → WIFIRESPONSE
        WIFIRECEIVED_/WIFIRECEIVE_ → WIFIRX (receive)
        WIFIRX_FRAME_*         → WIFIRXFRAME
        WIFIRX_*               → WIFIRX (receive processing)
        WIFITX_*               → WIFITX (transmit processing)
        """
        # Known multi-word prefixes
        prefixes_2 = [
            "WIFIMACTX", "WIFIMACRX", "WIFIPHYRX", "WIFIPHYTX",
            "WIFICOEX",  "WIFIPCU",   "WIFIOLE",   "WIFIREO",
            "WIFIWBM",   "WIFITQM",   "WIFIPDG",   "WIFIOFDMA",
            "WIFIXPCU",  "WIFIMIMO",  "WIFINA",    "WIFIDATA",
            "WIFIUNIFORM", "WIFIMPDU",
        ]
        # Three-word prefixes
        prefixes_3 = [
            "WIFISCHEDULER",
        ]

        for pfx in prefixes_2:
            if name.startswith(pfx + "_"):
                return pfx
        for pfx in prefixes_3:
            if name.startswith(pfx + "_"):
                return pfx

        # Handle TXPCU / RXPCU as compound
        if name.startswith("WIFITXPCU_"):
            return "WIFITXPCU"
        if name.startswith("WIFIRXPCU_"):
            return "WIFIRXPCU"

        # Remaining WIFI* prefixes: try splitting at second underscore
        parts = name.split("_", 2)
        if len(parts) >= 2 and parts[0] == "WIFI":
            return parts[0] + "_" + parts[1] if len(parts) >= 2 else parts[0]
        # Fallback
        return parts[0] if parts else "UNKNOWN"

    def lookup(self, tag_id: int) -> Optional[TlvTag]:
        """Look up a TLV tag by numeric ID."""
        return self.tags.get(tag_id)

    def lookup_by_name(self, name: str) -> Optional[TlvTag]:
        """Look up a TLV tag by name (exact match, case-insensitive)."""
        upper = name.upper()
        for tag in self.tags.values():
            if tag.name == upper:
                return tag
        return None

    def decode_header(self, data: bytes, offset: int = 0,
                      fmt: str | None = None) -> dict | None:
        """Decode a single TLV header from bytes at offset.

        Args:
            data: Raw byte buffer.
            offset: Start offset in data.
            fmt: Force format: 'tlv_16', 'tlv_32', or 'tlv_42'.
                 If None, auto-detect: try tlv_32 first (QCA6750 default),
                 then tlv_42, then tlv_16.

        Returns dict with: tag_id, tag_name, length, header_size,
        format, user_id (if applicable), or None if insufficient data.
        """
        remaining = len(data) - offset

        def _try_tlv_16():
            if remaining < 2:
                return None
            h16 = struct.unpack_from("<H", data, offset)[0]
            cflg = h16 & 1
            if cflg != 0:
                return None
            tag = (h16 >> 1) & 0x1F
            length = (h16 >> 6) & 0xF
            tag_info = self.lookup(tag)
            return {
                "offset": offset, "tag_id": tag,
                "tag_name": tag_info.name if tag_info else f"UNKNOWN_0x{tag:02x}",
                "length": length, "header_size": TLV_16_HDR_SIZE,
                "format": "tlv_16", "has_user_id": False,
                "raw_header": h16,
            }

        def _try_tlv_32():
            if remaining < 4:
                return None
            h32 = struct.unpack_from("<I", data, offset)[0]
            cflg = h32 & 1
            if cflg != 0:
                return None
            tag = (h32 >> 1) & 0x1FF
            length = (h32 >> 10) & 0xFFFF
            tag_info = self.lookup(tag)
            return {
                "offset": offset, "tag_id": tag,
                "tag_name": tag_info.name if tag_info else f"UNKNOWN_0x{tag:03x}",
                "length": length, "header_size": TLV_32_HDR_SIZE,
                "format": "tlv_32", "has_user_id": False,
                "raw_header": h32,
            }

        def _try_tlv_42():
            if remaining < 8:
                return None
            h64 = struct.unpack_from("<Q", data, offset)[0]
            compression = h64 & 1
            if compression != 1:
                return None
            tag = (h64 >> 1) & 0x1FF
            length = (h64 >> 10) & 0xFFFF
            usrid = (h64 >> 26) & 0x3F
            tag_info = self.lookup(tag)
            return {
                "offset": offset, "tag_id": tag,
                "tag_name": tag_info.name if tag_info else f"UNKNOWN_0x{tag:03x}",
                "length": length, "header_size": TLV_42_HDR_SIZE,
                "format": "tlv_42", "has_user_id": True,
                "user_id": usrid, "raw_header": h64,
            }

        if fmt == "tlv_16":
            return _try_tlv_16()
        elif fmt == "tlv_32":
            return _try_tlv_32()
        elif fmt == "tlv_42":
            return _try_tlv_42()

        # Auto-detect: try 32-bit first (QCA6750 default), then 42, then 16
        result = _try_tlv_32()
        if result:
            return result
        result = _try_tlv_42()
        if result:
            return result
        return _try_tlv_16()

    def decode_stream(self, data: bytes, max_items: int = 100,
                      default_fmt: str | None = None) -> list[dict]:
        """Decode a stream of TLV headers.

        Args:
            data: Raw byte buffer.
            max_items: Max number of items to decode.
            default_fmt: Format hint for all items (None = auto-detect).
        """
        results = []
        offset = 0
        while offset < len(data) and len(results) < max_items:
            hdr = self.decode_header(data, offset, fmt=default_fmt)
            if hdr is None or "error" in hdr:
                break
            results.append(hdr)
            offset += hdr["header_size"] + hdr["length"]
        return results

    def dump_categories(self) -> str:
        """Return a summary of TLV tags by category."""
        lines = []
        for cat in sorted(self.categories):
            tags = self.categories[cat]
            lines.append(f"\n## {cat} ({len(tags)} tags)")
            for t in sorted(tags, key=lambda x: x.tag_id):
                lines.append(f"  {t.tag_id:3d} (0x{t.tag_id:02x})  {t.name}")
        return "\n".join(lines)

    def dump_all_tags(self) -> str:
        """Return all TLV tags sorted by ID."""
        lines = []
        for tag_id in sorted(self.tags):
            t = self.tags[tag_id]
            lines.append(f"  {t.tag_id:3d} (0x{t.tag_id:02x})  [{t.category}]  {t.name}")
        return "\n".join(lines)

    @property
    def count(self) -> int:
        return len(self.tags)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="WCN6750 TLV decoder — parse and query hardware TLV tags"
    )
    parser.add_argument(
        "--tag-file",
        help="Path to tlv_tag_def.h (auto-located if omitted)",
    )
    parser.add_argument(
        "--parse", metavar="FILE",
        help="Parse tlv_tag_def.h from FILE and print summary",
    )
    parser.add_argument(
        "--lookup", metavar="ID|NAME",
        help="Look up a TLV by numeric ID or exact name",
    )
    parser.add_argument(
        "--decode-hex", metavar="HEX",
        help="Decode a hex-encoded TLV stream (e.g. '00102030...')",
    )
    parser.add_argument(
        "--dump-categories", action="store_true",
        help="Dump all TLV tags grouped by category",
    )
    parser.add_argument(
        "--dump-all", action="store_true",
        help="Dump all TLV tags sorted by ID",
    )

    args = parser.parse_args()
    tag_file = args.tag_file or args.parse

    decoder = TlvDecoder(tag_file=tag_file)

    if args.lookup:
        # Try numeric first, then by name
        try:
            tag_id = int(args.lookup, 0)
        except ValueError:
            tag_id = None

        if tag_id is not None:
            tag = decoder.lookup(tag_id)
        else:
            tag = decoder.lookup_by_name(args.lookup)

        if tag:
            print(f"Tag:  {tag.name}")
            print(f"ID:   {tag.tag_id} (0x{tag.tag_id:02x})")
            print(f"Cat:  {tag.category}")
        else:
            # Try partial match
            matches = [t for t in decoder.tags.values()
                       if args.lookup.upper() in t.name]
            if matches:
                print(f"Partial matches for '{args.lookup}':")
                for t in sorted(matches, key=lambda x: x.tag_id):
                    print(f"  {t.tag_id:3d} (0x{t.tag_id:02x})  [{t.category}]  {t.name}")
            else:
                print(f"Tag not found: {args.lookup}")
        return

    if args.decode_hex:
        try:
            data = bytes.fromhex(args.decode_hex.replace(" ", ""))
        except ValueError as e:
            print(f"Invalid hex: {e}")
            sys.exit(1)

        items = decoder.decode_stream(data)
        if not items:
            print("No TLV headers decoded")
            return

        for item in items:
            if "error" in item:
                print(f"@{item['offset']:04x}: ERROR: {item['error']}")
                continue
            user_info = f" usrid={item['user_id']}" if item.get('has_user_id') else ""
            print(
                f"@{item['offset']:04x}: "
                f"tag={item['tag_id']:3d} ({item['tag_name']}) "
                f"len={item['length']:5d} "
                f"hdr={item['header_size']}B "
                f"fmt={item['format']}"
                f"{user_info}"
            )
        return

    if args.dump_categories:
        print(decoder.dump_categories())
        return

    if args.dump_all:
        print(decoder.dump_all_tags())
        return

    # Default: summary
    print(f"Loaded {decoder.count} TLV tags")
    print(f"Categories: {len(decoder.categories)}")
    for cat in sorted(decoder.categories):
        print(f"  {cat}: {len(decoder.categories[cat])} tags")


if __name__ == "__main__":
    main()
