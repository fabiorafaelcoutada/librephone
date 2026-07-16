#!/usr/bin/env python3

# Copyright (c) 2026 Free Software Foundation, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""MBN/MDT file parser in PIL (Qualcomm Peripheral Image Loader) format.

Parses ELF32/ELF64 headers, segment tables, entry points,
and extracts relevant metadata for WPSS firmware analysis.

Usage:
    from tools.librephone.mbn_parser import parse_mbn, extract_sections

    parsed = parse_mbn("wlanmdsp.mbn")
    print(parsed["entry_point"])

    sections = extract_sections(parsed)
    print(sections["code"])
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "MBNParseError",
    "MBNFormatError",
    "parse_mbn",
    "extract_sections",
    "get_mbn_metadata",
]


class MBNParseError(ValueError):
    """Error al parsear un archivo MBN — archivo corrupto o truncado."""


class MBNFormatError(ValueError):
    """Formato MBN no soportado (no ELF, no PIL, o versión desconocida)."""


# ── Constantes ELF ─────────────────────────────────────────────────────────

_ELF_MAGIC = b"\x7fELF"
_EI_CLASS_32 = 1
_EI_CLASS_64 = 2
_EI_DATA_2LSB = 1  # little-endian
_EI_DATA_2MSB = 2  # big-endian
_ET_EXEC = 2
_ET_DYN = 3

# Tipos de sección ELF comunes
_SHT_TYPES = {
    0: "NULL",
    1: "PROGBITS",
    2: "SYMTAB",
    3: "STRTAB",
    4: "RELA",
    5: "HASH",
    6: "DYNAMIC",
    7: "NOTE",
    8: "NOBITS",
    9: "REL",
    11: "DYNSYM",
}

# Marcas de segmentos PIL Qualcomm
_PHDR_TYPE_LOAD = 1
_PHDR_TYPE_DYNAMIC = 2

# ── Elf Header (32-bit) ────────────────────────────────────────────────────

_ELF32_EHDR_FMT = "<16sHHIIIIIHHHHHH"
_ELF32_EHDR_SIZE = struct.calcsize(_ELF32_EHDR_FMT)

_ELF64_EHDR_FMT = "<16sHHIQQQIHHHHHH"
_ELF64_EHDR_SIZE = struct.calcsize(_ELF64_EHDR_FMT)


def _parse_elf_header(data: bytes) -> Dict[str, Any]:
    if len(data) < 16 or data[:4] != _ELF_MAGIC:
        raise MBNFormatError("No es un archivo ELF válido (magic number incorrecto)")

    ei_class = data[4]
    ei_data = data[5]

    if ei_data == _EI_DATA_2MSB:
        raise MBNFormatError("ELF big-endian no soportado")

    if ei_class == _EI_CLASS_32:
        if len(data) < _ELF32_EHDR_SIZE:
            raise MBNParseError("Archivo ELF32 truncado: header incompleto")
        e_ident, e_type, e_machine, e_version, e_entry, e_phoff, \
            e_shoff, e_flags, e_ehsize, e_phentsize, e_phnum, \
            e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(_ELF32_EHDR_FMT, data)

        phoff = e_phoff
        phentsize = e_phentsize
        phnum = e_phnum
        shentsize = e_shentsize
        shnum = e_shnum
        shoff = e_shoff

        return {
            "format": "ELF32",
            "little_endian": True,
            "e_type": e_type,
            "e_machine": e_machine,
            "e_entry": e_entry,
            "e_phoff": phoff,
            "e_phentsize": phentsize,
            "e_phnum": phnum,
            "e_shoff": shoff,
            "e_shentsize": shentsize,
            "e_shnum": shnum,
            "e_shstrndx": e_shstrndx,
            "is_pil": e_type in (_ET_EXEC, _ET_DYN),
        }

    elif ei_class == _EI_CLASS_64:
        if len(data) < _ELF64_EHDR_SIZE:
            raise MBNParseError("Archivo ELF64 truncado: header incompleto")
        e_ident, e_type, e_machine, e_version, e_entry, e_phoff, \
            e_shoff, e_flags, e_ehsize, e_phentsize, e_phnum, \
            e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(_ELF64_EHDR_FMT, data)

        return {
            "format": "ELF64",
            "little_endian": True,
            "e_type": e_type,
            "e_machine": e_machine,
            "e_entry": e_entry,
            "e_phoff": e_phoff,
            "e_phentsize": e_phentsize,
            "e_phnum": e_phnum,
            "e_shoff": e_shoff,
            "e_shentsize": e_shentsize,
            "e_shnum": e_shnum,
            "e_shstrndx": e_shstrndx,
            "is_pil": e_type in (_ET_EXEC, _ET_DYN),
        }

    else:
        raise MBNFormatError(f"Clase ELF no soportada: {ei_class}")


def _parse_phdr32(data: bytes, offset: int) -> Dict[str, Any]:
    fmt = "<IIIIIIII"
    size = struct.calcsize(fmt)
    chunk = data[offset : offset + size]
    if len(chunk) < size:
        raise MBNParseError(f"Segment header ELF32 truncado en offset 0x{offset:x}")
    p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = (
        struct.unpack_from(fmt, chunk)
    )
    return {
        "p_type": p_type,
        "p_offset": p_offset,
        "p_vaddr": p_vaddr,
        "p_paddr": p_paddr,
        "p_filesz": p_filesz,
        "p_memsz": p_memsz,
        "p_flags": p_flags,
        "p_align": p_align,
    }


def _parse_phdr64(data: bytes, offset: int) -> Dict[str, Any]:
    fmt = "<IIQQQQQQ"
    size = struct.calcsize(fmt)
    chunk = data[offset : offset + size]
    if len(chunk) < size:
        raise MBNParseError(f"Segment header ELF64 truncado en offset 0x{offset:x}")
    p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = (
        struct.unpack_from(fmt, chunk)
    )
    return {
        "p_type": p_type,
        "p_offset": p_offset,
        "p_vaddr": p_vaddr,
        "p_paddr": p_paddr,
        "p_filesz": p_filesz,
        "p_memsz": p_memsz,
        "p_flags": p_flags,
        "p_align": p_align,
    }


# ── API pública ────────────────────────────────────────────────────────────


def parse_mbn(filepath: str) -> Dict[str, Any]:
    """Parsea un archivo MBN extrayendo headers ELF y tabla de segmentos.

    Args:
        filepath: Ruta al archivo .mbn.

    Returns:
        Diccionario con formato, entry_point, segmentos y certificados.

    Raises:
        MBNFormatError: si el archivo no es ELF o PIL.
        MBNParseError: si el archivo está corrupto o truncado.
    """
    path = Path(filepath)
    raw = path.read_bytes()
    file_size = len(raw)

    elf_hdr = _parse_elf_header(raw)
    is_64bit = elf_hdr["format"] == "ELF64"

    # Parsear segment headers (program headers)
    segments = []
    phoff = elf_hdr["e_phoff"]
    phentsize = elf_hdr["e_phentsize"]
    phnum = elf_hdr["e_phnum"]

    # Detectar certificados X.509 v3 DER al final del archivo
    cert_count = 0
    pos = file_size
    while pos >= 4:
        # Buscar secuencia DER (0x30 0x82 ...)
        if pos + 4 <= file_size and raw[pos : pos + 2] == b"\x30\x82":
            try:
                cert_len = struct.unpack_from(">H", raw, pos + 2)[0] + 4
                if pos + cert_len <= file_size:
                    cert_count += 1
                    pos -= 1
                else:
                    break
            except struct.error:
                break
        else:
            break

    for i in range(phnum):
        off = phoff + i * phentsize
        if is_64bit:
            seg = _parse_phdr64(raw, off)
        else:
            seg = _parse_phdr32(raw, off)
        seg["segment_index"] = i
        segments.append(seg)

    # Clasificar segmentos
    pil_segments = []
    for seg in segments:
        seg_type_desc = _SHT_TYPES.get(seg["p_type"], f"0x{seg['p_type']:x}")
        pil_segments.append({
            "index": seg["segment_index"],
            "type": seg_type_desc,
            "offset": seg["p_offset"],
            "vaddr": seg["p_vaddr"],
            "paddr": seg["p_paddr"],
            "file_size": seg["p_filesz"],
            "mem_size": seg["p_memsz"],
            "flags": seg["p_flags"],
            "is_load": seg["p_type"] == _PHDR_TYPE_LOAD,
        })

    return {
        "file": path.name,
        "format": elf_hdr["format"],
        "entry_point": f"0x{elf_hdr['e_entry']:x}" if is_64bit else f"0x{elf_hdr['e_entry']:08x}",
        "segments": pil_segments,
        "certificates": cert_count,
        "size_bytes": file_size,
        "md5": hashlib.md5(raw).hexdigest(),
    }


def extract_sections(parsed: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Clasifica las secciones/segmentos de un MBN parseado.

    Args:
        parsed: Resultado de parse_mbn().

    Returns:
        Diccionario con listas de segmentos clasificados: code, data, bss, certs.
    """
    sections: Dict[str, List[Dict[str, Any]]] = {
        "code": [],
        "data": [],
        "bss": [],
        "certificates": [],
        "other": [],
    }

    # Los certificados están al final del archivo
    if parsed["certificates"] > 0:
        sections["certificates"].append({
            "count": parsed["certificates"],
            "offset": parsed["size_bytes"] - parsed["certificates"] * 1024,
            "size_estimated": parsed["certificates"] * 1024,
        })

    for seg in parsed["segments"]:
        entry = {
            "index": seg["index"],
            "type": seg["type"],
            "offset": seg["offset"],
            "vaddr": seg["vaddr"],
            "size": seg["file_size"],
        }

        if seg["is_load"]:
            # .bss tiene file_size = 0 (solo ocupa memoria)
            if seg["file_size"] == 0 and seg["mem_size"] > 0:
                sections["bss"].append(entry)
            elif seg["flags"] & 1:  # PF_X = executable
                sections["code"].append(entry)
            else:
                sections["data"].append(entry)
        else:
            sections["other"].append(entry)

    return sections


def get_mbn_metadata(filepath: str) -> Dict[str, Any]:
    """Obtiene metadatos resumidos de un archivo MBN.

    Args:
        filepath: Ruta al archivo .mbn.

    Returns:
        Diccionario con versión, checksum, firmware ID y tamaño.
    """
    parsed = parse_mbn(filepath)
    sections = extract_sections(parsed)

    total_code = sum(s["size"] for s in sections["code"])
    total_data = sum(s["size"] for s in sections["data"])
    total_bss = sum(s["size"] for s in sections["bss"])

    firmware_id = None
    for seg in parsed["segments"]:
        if seg["is_load"] and seg["vaddr"] != 0:
            firmware_id = f"pil@{seg['vaddr']:x}"
            break

    return {
        "file": parsed["file"],
        "format": parsed["format"],
        "entry_point": parsed["entry_point"],
        "firmware_id": firmware_id,
        "size_bytes": parsed["size_bytes"],
        "md5": parsed["md5"],
        "segments": len(parsed["segments"]),
        "certificates": parsed["certificates"],
        "sizes": {
            "code_total": total_code,
            "data_total": total_data,
            "bss_total": total_bss,
        },
    }
