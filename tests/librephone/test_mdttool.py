#!/usr/bin/env python3
"""Tests for librephone.mdttool."""

from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest

from librephone.mdttool import MDTTool


# ── Helpers to construct synthetic ELF files ────────────────────────────────

def _build_elf32_minimal() -> bytes:
    """Build a minimal ELF32 executable with 2 program headers and 0 sections."""
    # e_ident: 16 bytes
    e_ident = b"\x7fELF\x01\x01\x01\x00\x00" + b"\x00" * 7
    assert len(e_ident) == 16

    # e_phoff = 52 (16-byte magic + 36-byte ELF32 header)
    ehdr = struct.pack(
        "<16sHHIIIIIHHHHHH",
        e_ident,         # e_ident
        2,               # e_type = ET_EXEC
        0x28,            # e_machine = EM_ARM
        1,               # e_version
        0x80000000,      # e_entry
        0x34,            # e_phoff = 52
        0,               # e_shoff = 0 (no sections)
        0,               # e_flags
        52,              # e_ehsize
        32,              # e_phentsize
        2,               # e_phnum
        40,              # e_shentsize
        0,               # e_shnum = 0
        0,               # e_shstrndx
    )

    # Program header 1: .text — executable + readable
    phdr1 = struct.pack(
        "<IIIIIIII",
        1,              # p_type = PT_LOAD
        0x80,           # p_offset
        0x80000080,     # p_vaddr
        0x80000080,     # p_paddr
        64,             # p_filesz
        64,             # p_memsz
        0x5,            # p_flags = PF_R | PF_X
        64,             # p_align
    )

    # Program header 2: .data — readable + writable
    phdr2 = struct.pack(
        "<IIIIIIII",
        1,              # p_type = PT_LOAD
        0xC0,           # p_offset
        0x800000C0,     # p_vaddr
        0x800000C0,     # p_paddr
        32,             # p_filesz
        32,             # p_memsz
        0x6,            # p_flags = PF_R | PF_W
        64,             # p_align
    )

    payload = ehdr + phdr1 + phdr2
    payload += b"\x00" * 64   # .text content (64 bytes of zeros)
    payload += b"\x01" * 32   # .data content (32 bytes of ones)
    return payload


def _build_elf64_minimal() -> bytes:
    """Build a minimal ELF64 executable with 2 program headers and 0 sections."""
    e_ident = b"\x7fELF\x02\x01\x01\x00\x00" + b"\x00" * 7
    assert len(e_ident) == 16

    # ELF64 header: e_phoff = 64 (16-byte magic + 48-byte ELF64 header)
    ehdr = struct.pack(
        "<16sHHIQQQIHHHHHH",
        e_ident,         # e_ident
        2,               # e_type = ET_EXEC
        0xB7,            # e_machine = EM_AARCH64
        1,               # e_version
        0x8000000000,    # e_entry
        0x40,            # e_phoff = 64
        0,               # e_shoff = 0 (no sections)
        0,               # e_flags
        64,              # e_ehsize
        56,              # e_phentsize
        2,               # e_phnum
        64,              # e_shentsize
        0,               # e_shnum = 0
        0,               # e_shstrndx
    )

    # ELF64 Program header 1 — .text
    phdr1 = struct.pack(
        "<IIQQQQQQ",
        1,              # p_type = PT_LOAD
        0x5,            # p_flags = PF_R | PF_X
        0x80,           # p_offset
        0x80000080,     # p_vaddr
        0x80000080,     # p_paddr
        64,             # p_filesz
        64,             # p_memsz
        64,             # p_align
    )

    # ELF64 Program header 2 — .data
    phdr2 = struct.pack(
        "<IIQQQQQQ",
        1,              # p_type = PT_LOAD
        0x6,            # p_flags = PF_R | PF_W
        0xC0,           # p_offset
        0x800000C0,     # p_vaddr
        0x800000C0,     # p_paddr
        32,             # p_filesz
        32,             # p_memsz
        64,             # p_align
    )

    payload = ehdr + phdr1 + phdr2
    payload += b"\x00" * 64   # .text content
    payload += b"\x01" * 32   # .data content
    return payload


def _build_elf32_with_sections() -> bytes:
    """Build an ELF32 with sections (no program headers). For linking, not exec."""
    e_ident = b"\x7fELF\x01\x01\x01\x00\x00" + b"\x00" * 7
    assert len(e_ident) == 16

    # e_shoff = 52 (16-byte magic + 36-byte ELF32 header)
    ehdr = struct.pack(
        "<16sHHIIIIIHHHHHH",
        e_ident,         # e_ident
        1,               # e_type = ET_REL
        0x28,            # e_machine = EM_ARM
        1,               # e_version
        0,               # e_entry
        0,               # e_phoff = 0 (no program headers)
        0x34,            # e_shoff = 52
        0,               # e_flags
        52,              # e_ehsize
        0,               # e_phentsize = 0
        0,               # e_phnum = 0
        40,              # e_shentsize
        2,               # e_shnum = 2
        1,               # e_shstrndx = 1
    )

    # Section header 0: SHT_NULL (required, all zeros)
    shdr0 = struct.pack(
        "<IIIIIIIIII",
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    )

    # Section header 1: .text — SHT_PROGBITS, content at offset 0x84
    shdr1 = struct.pack(
        "<IIIIIIIIII",
        0x1B,           # sh_name (offset in .shstrtab, arbitrary)
        1,              # sh_type = SHT_PROGBITS
        0x6,            # sh_flags = SHF_ALLOC | SHF_EXECINSTR
        0x80000000,     # sh_addr
        0x84,           # sh_offset (52 + 40 + 40 = 0x84)
        64,             # sh_size
        0,              # sh_link
        0,              # sh_info
        64,             # sh_addralign
        0,              # sh_entsize
    )

    payload = ehdr + shdr0 + shdr1
    payload += b"\x00" * 64   # .text content
    return payload


def _build_non_elf() -> bytes:
    """Build a file that looks nothing like an ELF."""
    return b"\xDE\xAD\xBE\xEF" + b"\x00" * 100


def _build_with_der_certs() -> bytes:
    """Build a minimal ELF32 plus embedded DER-encoded data sequences.

    DER certs start with 0x30 0x82 (SEQUENCE + 2-byte length).
    This creates two fake cert-like regions after the ELF data.
    """
    base = _build_elf32_minimal()

    # Fake DER cert 1: 0x30 0x82 followed by length=50 bytes of zeros
    cert1 = b"\x30\x82" + struct.pack(">H", 50) + b"\x00" * 50

    # Fake DER cert 2: 0x30 0x82 followed by length=30 bytes of ones
    cert2 = b"\x30\x82" + struct.pack(">H", 30) + b"\x01" * 30

    return base + cert1 + cert2


# ── Constructor tests ───────────────────────────────────────────────────────

class TestConstructor:
    """Tests for MDTTool.__init__()."""

    def test_init_no_args(self):
        """Constructor should work with no arguments."""
        tool = MDTTool()
        assert tool.mdtfile is None
        assert tool.elf_header == {}
        assert tool.magic == {}
        assert tool.seg_headers == []
        assert tool.prog_headers == []

    def test_init_with_mdt_file_cleans_elf(self, tmp_path):
        """With .mdt file, existing .elf should be cleaned up."""
        # Create a .mdt file (synthetic ELF32)
        mdt_path = tmp_path / "test.mdt"
        mdt_path.write_bytes(_build_elf32_minimal())

        # Create a stale .elf file
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(b"stale elf data")

        assert elf_path.exists()
        MDTTool(str(mdt_path))
        assert not elf_path.exists(), "Stale .elf file should be cleaned up"

    def test_init_with_non_mdt_does_not_delete(self, tmp_path):
        """Constructor MUST NOT delete files that lack .mdt extension.

        This is a regression test for the os.remove() bug where
        wpss.mbn files were being deleted because str.replace(".mdt", ".elf")
        was a no-op on non-.mdt filenames.
        """
        # Create a .mbn file (simulating wpss.mbn)
        mbn_path = tmp_path / "wpss.mbn"
        mbn_path.write_bytes(_build_elf32_minimal())

        assert mbn_path.exists()
        MDTTool(str(mbn_path))
        assert mbn_path.exists(), (
            "CRITICAL BUG: Constructor deleted the input file!\n"
            "'mdtfile.replace('.mdt', '.elf')' was a no-op for non-.mdt "
            "filenames, which caused os.remove() to delete the original file."
        )

    def test_init_with_nonexistent_mdt_does_not_crash(self, tmp_path):
        """Constructor should handle nonexistent file paths gracefully."""
        nonexistent = tmp_path / "nonexistent.mdt"
        tool = MDTTool(str(nonexistent))
        assert tool.mdtfile == nonexistent
        # No crash is the pass condition. The file path is stored but
        # nothing tries to open it in __init__.


# ── Magic number tests ──────────────────────────────────────────────────────

class TestReadMagic:
    """Tests for read_magic()."""

    def test_read_magic_elf32(self, tmp_path):
        """read_magic() should correctly parse ELF32 magic."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf32_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        magic = tool.read_magic()

        assert magic["ei_class"] == 0x1, "ei_class 0x1 = 32-bit"
        assert magic["ei_data"] == 0x1, "ei_data 0x1 = little-endian"
        assert magic["ei_version"] == 0x1

    def test_read_magic_elf64(self, tmp_path):
        """read_magic() should correctly parse ELF64 magic."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf64_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        magic = tool.read_magic()

        assert magic["ei_class"] == 0x2, "ei_class 0x2 = 64-bit"
        assert magic["ei_data"] == 0x1, "ei_data 0x1 = little-endian"

    def test_read_magic_non_elf(self, tmp_path):
        """read_magic() should return empty dict for non-ELF files."""
        path = tmp_path / "not_elf.bin"
        path.write_bytes(_build_non_elf())

        tool = MDTTool()
        tool.infile = open(str(path), "rb")
        magic = tool.read_magic()

        assert magic == {}, "Non-ELF files should return empty dict"


# ── ELF32 parsing tests ─────────────────────────────────────────────────────

class TestELF32:
    """Tests for ELF32 header and program header parsing."""

    def test_read_elf32_header(self, tmp_path):
        """read_elf32() should parse all header fields correctly."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf32_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        tool.read_magic()  # Must read magic first (consumes 16 bytes)
        elf_hdr = tool.read_elf32()

        assert elf_hdr["e_type"] == 2, "ET_EXEC"
        assert elf_hdr["e_machine"] == 0x28, "EM_ARM"
        assert elf_hdr["e_version"] == 1
        assert elf_hdr["e_entry"] == 0x80000000
        assert elf_hdr["e_phoff"] == 0x34
        assert elf_hdr["e_shoff"] == 0
        assert elf_hdr["e_ehsize"] == 52
        assert elf_hdr["e_phentsize"] == 32
        assert elf_hdr["e_phnum"] == 2
        assert elf_hdr["e_shentsize"] == 40
        assert elf_hdr["e_shnum"] == 0

    def test_read_program_header32(self, tmp_path):
        """read_program_header32() should parse PT_LOAD correctly."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf32_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        tool.read_magic()  # Must read magic first (consumes 16 bytes)
        tool.elf_header = tool.read_elf32()

        # Seek to first program header
        tool.infile.seek(tool.elf_header["e_phoff"], 0)

        phdr = tool.read_program_header32()
        assert phdr["p_type"] == 1, "PT_LOAD"
        assert phdr["p_offset"] == 0x80
        assert phdr["p_vaddr"] == 0x80000080
        assert phdr["p_filesz"] == 64
        assert phdr["p_memsz"] == 64
        assert phdr["p_flags"] & 0x1, "PF_X should be set"
        assert phdr["p_flags"] & 0x4, "PF_R should be set"

    def test_read_section_header32(self, tmp_path):
        """read_section_header32() should parse SHT_PROGBITS correctly."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf32_with_sections())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        tool.read_magic()
        tool.elf_header = tool.read_elf32()

        # Seek to first section header (SHT_NULL)
        tool.infile.seek(tool.elf_header["e_shoff"], 0)

        # First section header is SHT_NULL
        shdr_null = tool.read_section_header32()
        assert shdr_null["sh_type"] == 0, "SHT_NULL"

        # Second section header is .text
        shdr_text = tool.read_section_header32()
        assert shdr_text["sh_type"] == 1, "SHT_PROGBITS"
        assert shdr_text["sh_size"] == 64


# ── ELF64 parsing tests ─────────────────────────────────────────────────────

class TestELF64:
    """Tests for ELF64 header and program header parsing."""

    def test_read_elf64_header(self, tmp_path):
        """read_elf64() should parse all header fields correctly."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf64_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        tool.read_magic()
        tool.elf_header = tool.read_elf64()

        assert tool.elf_header["e_type"] == 2, "ET_EXEC"
        assert tool.elf_header["e_machine"] == 0xB7, "EM_AARCH64"
        assert tool.elf_header["e_version"] == 1
        assert tool.elf_header["e_phoff"] == 0x40
        assert tool.elf_header["e_shoff"] == 0
        assert tool.elf_header["e_ehsize"] == 64
        assert tool.elf_header["e_phentsize"] == 56
        assert tool.elf_header["e_phnum"] == 2

    def test_read_program_header64(self, tmp_path):
        """read_program_header64() should parse PT_LOAD correctly."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf64_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        tool.read_magic()
        tool.elf_header = tool.read_elf64()

        # Seek to first program header
        tool.infile.seek(tool.elf_header["e_phoff"], 0)

        phdr = tool.read_program_header64()
        assert phdr["p_type"] == 1, "PT_LOAD"
        assert phdr["p_offset"] == 0x80
        assert phdr["p_vaddr"] == 0x80000080
        assert phdr["p_filesz"] == 64
        assert phdr["p_memsz"] == 64

    def test_read_program_header64_second_entry(self, tmp_path):
        """read_program_header64() should parse the second PH correctly."""
        elf_path = tmp_path / "test.elf"
        elf_path.write_bytes(_build_elf64_minimal())

        tool = MDTTool()
        tool.infile = open(str(elf_path), "rb")
        tool.read_magic()
        tool.elf_header = tool.read_elf64()

        tool.infile.seek(tool.elf_header["e_phoff"], 0)
        tool.read_program_header64()

        phdr2 = tool.read_program_header64()
        assert phdr2["p_type"] == 1, "PT_LOAD"
        assert phdr2["p_offset"] == 0xC0
        assert phdr2["p_flags"] & 0x2, "PF_W should be set"


# ── read_mdt integration tests ──────────────────────────────────────────────

class TestReadMDT:
    """Integration tests for read_mdt()."""

    def test_read_mdt_elf32(self, tmp_path):
        """read_mdt() should parse a complete ELF32 with program headers."""
        mdt_path = tmp_path / "test.mdt"
        mdt_path.write_bytes(_build_elf32_minimal())

        tool = MDTTool(str(mdt_path))
        elf_hdr = tool.read_mdt(str(mdt_path))

        assert elf_hdr["e_type"] == 2
        assert elf_hdr["e_machine"] == 0x28
        assert elf_hdr["e_phnum"] == 2
        assert elf_hdr["e_shnum"] == 0, "No sections in this fixture"

        assert len(tool.prog_headers) == 2
        assert tool.prog_headers[0]["p_type"] == 1, "PT_LOAD"
        assert tool.prog_headers[1]["p_type"] == 1, "PT_LOAD"

    def test_read_mdt_elf64(self, tmp_path):
        """read_mdt() should parse a complete ELF64 with program headers."""
        mdt_path = tmp_path / "test.mdt"
        mdt_path.write_bytes(_build_elf64_minimal())

        tool = MDTTool(str(mdt_path))
        elf_hdr = tool.read_mdt(str(mdt_path))

        assert elf_hdr["e_type"] == 2
        assert elf_hdr["e_machine"] == 0xB7, "EM_AARCH64"
        assert elf_hdr["e_phnum"] == 2
        assert len(tool.prog_headers) == 2

    def test_read_mdt_elf32_with_sections(self, tmp_path):
        """read_mdt() should parse ELF32 with section headers."""
        mdt_path = tmp_path / "test.mdt"
        mdt_path.write_bytes(_build_elf32_with_sections())

        tool = MDTTool(str(mdt_path))
        elf_hdr = tool.read_mdt(str(mdt_path))

        assert elf_hdr["e_shnum"] == 2
        assert len(tool.seg_headers) == 2


# ── Certificate extraction tests ────────────────────────────────────────────

class TestGetCerts:
    """Tests for get_certs()."""

    def test_get_certs_finds_der_sequences(self, tmp_path):
        """get_certs() should find and extract DER cert sequences."""
        data = _build_with_der_certs()
        mbn_path = tmp_path / "test.mbn"
        mbn_path.write_bytes(data)

        tool = MDTTool(str(mbn_path))
        tool.read_mdt(str(mbn_path))
        tool.get_certs()

        # Two cert files should be created (names are hex offsets)
        cert_files = sorted(tmp_path.glob("*"))
        der_files = [f for f in cert_files if f.name != "test.mbn"]
        assert len(der_files) == 2, f"Expected 2 cert files, got {len(der_files)}: {[f.name for f in der_files]}"

    def test_get_certs_no_certs(self, tmp_path):
        """get_certs() should produce no files when there are no certs."""
        data = _build_elf32_minimal()
        mbn_path = tmp_path / "test.mbn"
        mbn_path.write_bytes(data)

        tool = MDTTool(str(mbn_path))
        tool.read_mdt(str(mbn_path))
        tool.get_certs()

        # No DER 0x30 0x82 sequences in this file
        der_files = [f for f in tmp_path.glob("*") if f.name != "test.mbn"]
        assert len(der_files) == 0, f"No cert files expected, got: {der_files}"


# ── merge_blobs tests ───────────────────────────────────────────────────────

class TestMergeBlobs:
    """Tests for merge_blobs()."""

    def test_merge_blobs_basic(self, tmp_path):
        """merge_blobs() should combine .b00 and .b01 into a single .elf."""
        # Create .b00 and .b01 files
        b00 = tmp_path / "test.b00"
        b00.write_bytes(b"AAAA" * 10)
        b01 = tmp_path / "test.b01"
        b01.write_bytes(b"BBBB" * 10)

        mdt_path = tmp_path / "test.mdt"
        mdt_path.write_bytes(_build_elf32_minimal())

        tool = MDTTool(str(mdt_path))
        tool.read_mdt(str(mdt_path))
        tool.merge_blobs(str(mdt_path))

        elf_path = tmp_path / "test.elf"
        assert elf_path.exists(), "Merged .elf file should exist"
        content = elf_path.read_bytes()
        assert b"AAAA" in content
        assert b"BBBB" in content

    def test_merge_blobs_wpss_rejected(self, tmp_path):
        """merge_blobs() should refuse to merge WPSS files."""
        # Create wpss.b* files
        b00 = tmp_path / "wpss.b00"
        b00.write_bytes(b"AAAA")
        b01 = tmp_path / "wpss.b01"
        b01.write_bytes(b"BBBB")

        mdt_path = tmp_path / "wpss.mdt"
        mdt_path.write_bytes(_build_elf32_minimal())

        tool = MDTTool(str(mdt_path))
        tool.read_mdt(str(mdt_path))
        result = tool.merge_blobs(str(mdt_path))

        assert result == 1, "WPSS merge should return 1 (error)"
        elf_path = tmp_path / "wpss.elf"
        assert not elf_path.exists(), "WPSS .elf should NOT be created"


# ── get_memsize tests ───────────────────────────────────────────────────────

class TestGetMemSize:
    """Tests for get_memsize()."""

    def test_get_memsize(self, tmp_path):
        """get_memsize() should return the memory region size."""
        data = _build_elf32_with_sections()
        mdt_path = tmp_path / "test.mdt"
        mdt_path.write_bytes(data)

        tool = MDTTool(str(mdt_path))
        tool.read_mdt(str(mdt_path))
        # get_memsize iterates e_shnum section headers
        memsize = tool.get_memsize()

        # With our fixture: first section at paddr 0, size 0
        # second section at paddr 0x80000000, size 64
        # max_addr = 0x80000000 + 64, min_addr = 0
        # result = (max_addr - min_addr) = 0x80000040
        assert memsize == 0x80000040
