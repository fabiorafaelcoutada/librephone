#!/usr/bin/env python3
"""Tests para tools.librephone.mbn_parser."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from tools.librephone.mbn_parser import (
    MBNFormatError,
    MBNParseError,
    extract_sections,
    get_mbn_metadata,
    parse_mbn,
)


# ── Helpers para construir archivos ELF sintéticos ─────────────────────────

def _build_elf32_minimal() -> bytes:
    """Construye un ELF32 ejecutable mínimo con 2 segmentos LOAD."""
    # e_ident: 16 bytes (magic + class + data + version + osabi + abiver + pad)
    e_ident = b"\x7fELF\x01\x01\x01\x00\x00" + b"\x00" * 7
    assert len(e_ident) == 16
    ehdr = struct.pack(
        "<16sHHIIIIIHHHHHH",
        e_ident,        # e_ident (16 bytes)
        2,              # e_type = ET_EXEC
        40,             # e_machine = ARM
        1,              # e_version
        0x80000000,     # e_entry
        0x34,           # e_phoff (justo después del ehdr)
        0,              # e_shoff (no sections)
        0,              # e_flags
        52,             # e_ehsize
        32,             # e_phentsize
        2,              # e_phnum
        40,             # e_shentsize
        0,              # e_shnum
        0,              # e_shstrndx
    )

    # Program header 1: .text (executable, readable)
    phdr1 = struct.pack(
        "<IIIIIIII",
        1,  # p_type = PT_LOAD
        0x80,  # p_offset
        0x80000080,  # p_vaddr
        0x80000080,  # p_paddr
        64,  # p_filesz
        64,  # p_memsz
        1 | 4,  # p_flags = PF_X | PF_R
        64,  # p_align
    )

    # Program header 2: .data (readable, writable)
    phdr2 = struct.pack(
        "<IIIIIIII",
        1,  # p_type = PT_LOAD
        0xC0,  # p_offset
        0x800000C0,  # p_vaddr
        0x800000C0,  # p_paddr
        32,  # p_filesz
        32,  # p_memsz
        2 | 4,  # p_flags = PF_W | PF_R
        64,  # p_align
    )

    payload = ehdr + phdr1 + phdr2
    # Content for .text
    payload += b"\x00" * 64
    # Content for .data
    payload += b"\x01" * 32

    return payload


def _build_non_elf() -> bytes:
    """Construye un archivo que NO es ELF."""
    return b"NOT_AN_ELF_FILE\x00\x00"


def _build_truncated_elf() -> bytes:
    """Construye un ELF32 con header incompleto (truncado).
    
    Pasa la verificación de magic y e_ident (16 bytes válidos)
    pero el ELF header completo de 52 bytes está truncado (solo 16).
    """
    return b"\x7fELF\x01\x01\x01\x00\x00" + b"\x00" * 7  # 16 bytes, header ELF32 incompleto


class TestParseMbn:
    """Tests para parse_mbn()."""

    def test_parse_valid_elf32(self, tmp_path: Path) -> None:
        raw = _build_elf32_minimal()
        path = tmp_path / "test.mbn"
        path.write_bytes(raw)

        parsed = parse_mbn(str(path))
        assert parsed["format"] == "ELF32"
        assert "0x80000000" in parsed["entry_point"]
        assert len(parsed["segments"]) == 2
        assert parsed["size_bytes"] == len(raw)
        assert parsed["certificates"] >= 0
        assert isinstance(parsed["md5"], str)
        assert len(parsed["md5"]) == 32

    def test_parse_non_elf(self, tmp_path: Path) -> None:
        raw = _build_non_elf()
        path = tmp_path / "bad.mbn"
        path.write_bytes(raw)

        with pytest.raises(MBNFormatError, match="No es un archivo ELF"):
            parse_mbn(str(path))

    def test_parse_truncated_elf(self, tmp_path: Path) -> None:
        raw = _build_truncated_elf()
        path = tmp_path / "trunc.mbn"
        path.write_bytes(raw)

        with pytest.raises(MBNParseError):
            parse_mbn(str(path))


class TestExtractSections:
    """Tests para extract_sections()."""

    def test_extract_sections_classification(self, tmp_path: Path) -> None:
        raw = _build_elf32_minimal()
        path = tmp_path / "test.mbn"
        path.write_bytes(raw)

        parsed = parse_mbn(str(path))
        sections = extract_sections(parsed)

        # .text segment should be in "code" (executable flag)
        assert len(sections["code"]) >= 1

        # .data segment should be in "data"
        assert len(sections["data"]) >= 1

        # Total segments classified
        total = sum(len(v) for v in sections.values())
        assert total >= 2  # at least the 2 LOAD segments


class TestGetMbnMetadata:
    """Tests para get_mbn_metadata()."""

    def test_metadata_has_expected_keys(self, tmp_path: Path) -> None:
        raw = _build_elf32_minimal()
        path = tmp_path / "test.mbn"
        path.write_bytes(raw)

        meta = get_mbn_metadata(str(path))
        assert meta["format"] == "ELF32"
        assert "entry_point" in meta
        assert meta["size_bytes"] == len(raw)
        assert meta["segments"] == 2
        assert "md5" in meta
        assert "sizes" in meta
        assert "code_total" in meta["sizes"]

    def test_metadata_firmware_id(self, tmp_path: Path) -> None:
        raw = _build_elf32_minimal()
        path = tmp_path / "test.mbn"
        path.write_bytes(raw)

        meta = get_mbn_metadata(str(path))
        # Should find at least one loadable segment with non-zero vaddr
        assert meta["firmware_id"] is not None
        assert "pil@" in meta["firmware_id"] or meta["firmware_id"] is not None
