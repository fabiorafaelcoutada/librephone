#!/usr/bin/python3

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

# base class to contain device data
import argparse
import logging
import os
from sys import argv
import sys
from pathlib import Path
import re
import struct
import hashlib
import binascii
from enum import IntEnum
from glob import glob
from pprint import pprint

import librephone as lp
rootdir = lp.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

DataSizes = {
    "Elf32_Addr": 4,
    "Elf64_Addr": 8,
    "Elf32_Half": 2,
    "Elf32_SHalf": 2,
    "Elf64_Half": 2,
    "Elf32_Off": 4,
    "Elf64_Off": 8,
    "Elf32_Word": 4,
    "Elf64_Word": 4,
    "Elf32_SWord": 4,
    "Elf64_XWord": 8,
    "Elf64_SWord": 4,
    "Elf64_Sxword": 8,
    }

StructTypes = {
    "Elf32_Addr": "<I",
    "Elf64_Addr": "<Q",
    "Elf32_Half": "<H",
    "Elf32_SHalf": "<h",
    "Elf64_Half": "<H",
    "Elf32_Off": "<I",
    "Elf64_Off": "<Q",
    "Elf32_Word": "<I",
    "Elf64_Word": "<I",
    "Elf32_SWord": "<i",
    "Elf64_XWord": "<Q",
    "Elf64_SWord": "<I",
    "Elf64_Sxword": "<Q",
    }

ProgTypes = [
    "PT_NULL",
    "PT_LOAD",
    "PT_DYNAMIC",
    "PT_INTERP",
    "PT_NOTE",
    "PT_SHLIB",
    "PT_PHDR"
    ]

SegTypes = [
	"SHT_NULL",
	"SHT_PROGBITS",
	"SHT_SYMTAB",
	"SHT_STRTAB",
	"SHT_RELA",
	"SHT_HASH",
	"SHT_DYNAMIC",
	"SHT_NOTE",
	"SHT_NOBITS",
	"SHT_REL",
	"SHT_SHLIB",
	"SHT_DYNSYM",
	"SHT_NUM",
    ]

SegFlags = {
	"SHF_WRITE": 0x1,
	"SHF_ALLOC": 0x2,
	"SHF_EXECINSTR": 0x4,
	"SHF_MERGE": 0x10,
	"SHF_STRINGS": 0x20,
	"SHF_INFO_LINK": 0x40,
	"SHF_LINK_ORDER": 0x80,
	"SHF_OS_NONCONFORMING": 0x100,
	"SHF_GROUP": 0x200,
	"SHF_TLS": 0x400,
	"SHF_RELA_LIVEPATCH": 0x00100000,
	"SHF_RO_AFTER_INIT": 0x00200000,
	"SHF_ORDERED": 0x04000000,
	"SHF_EXCLUDE": 0x08000000,
	"SHF_MASKOS": 0x0ff00000,
	"SHF_MASKPROC": 0xf0000000,
    }

SegNames = {
    "None": 0x0,
    ".note.gnu.build-id": 0x1b,
    ".init": 0x2e,
    ".text": 0x34,
    ".fini": 0x3a,
    ".rodata": 0x40,
    ".eh_frame": 0x48,
    ".init_array": 0x52,
    ".fini_array": 0x5e,
    ".got": 0x6a,
    ".got.plt": 0x6f,
    ".data": 0x78,
    ".bss": 0x7e,
    ".comment": 0x83,
    ".debug_aranges": 0x9b,
    ".debug_info": 0xa7,
    ".debug_abbrev": 0xb5,
    ".debug_line": 0xc1,
    ".debug_frame": 0xce,
    ".debug_str": 0xd9,
    ".debug_line_str": 0xe9,
    ".debug_loclists": 0xf9,
    ".debug_rnglists":0x1,
    ".symtab": 0x9,
    ".strtab": 0x11,
    }

PflagPerms = {
    "PF_R": 0x4, # 100 binary
    "PF_W": 0x2, # 10 binary
    "PF_X": 0x1, # 1  binary
    }


# This program does multiple reads of the same file, so if you screw up
# the size of a data field, all the following ones will be wrong.
class MDTTool(object):
    def __init__(self,
                 mdtfile: str() = None,
                 outdir: str() = None,
                 ):
        """
        Returns:
            (MDTool): An instance of this class

        Args:
            mdtfile (str): The MDT file
            outdir (str): output directory
        """
        if mdtfile:
            self.mdtfile = Path(mdtfile)
            output = mdtfile.replace(".mdt", ".elf")
            if os.path.exists(output):
                os.remove(output)
            #self.outfile = open(output, "ab")
            # self.infile = open(mdtfile, "rb")
        else:
            self.mdtfile = None
            self.outfile = None
            self.infile = None

        self.elf_header = dict()
        self.magic = dict()
        self.seg_headers = list()
        self.prog_headers = list()
        
    def read_mdt(self,
                 mdtfile: str = None,
                 ):
        """
        An MDT file contains an EL:F file that specifies the program segments,
        followed by 3 SSL certificates.

        Args:
            mdtfile (str): The MDT file to parse.
        """
        if mdtfile:
            self.mdtfile = Path(mdtfile)
            # output = mdtfile.replace(".mdt", ".elf")
            # if os.path.exists(output):
            #     os.remove(output)
            # self.outfile = open(output, "ab")
            self.infile = open(mdtfile, "rb")
        elif self.mdtfile:
            mdt = open(self.mdtfile, "rb")

        self.read_magic()

        if self.magic["ei_class"] == 0x2:
            self.elf_header = self.read_elf64()
        elif self.magic["ei_class"] == 0x1:
            self.elf_header = self.read_elf32()

        # print("Dumping ELF Header")
        self.dump_header(self.elf_header)

        loc = self.infile.seek(self.elf_header["e_phoff"], 0)
        for i in range(0, self.elf_header["e_phnum"]):
            if self.magic["ei_class"] == 0x2:
                data = self.read_program_header64()
            elif self.magic["ei_class"] == 0x1:
                data = self.read_program_header32()
            # print("Dumping program header")
            # self.dump_header(data)
            # self.seg_headers.append(data)

        loc = self.infile.seek(self.elf_header["e_shoff"], 0)
        for i in range(0, self.elf_header["e_shnum"]):
            data = self.read_section_header64()
            # print("Dumping segment header")
            # self.dump_header(data)
            self.seg_headers.append(data)

    def read_magic(self,
                   ) -> dict:
        """
        """
        # The ELF header is always 16 bytes
        magic = self.infile.read(16)

        # print(f"MAGIC: {binascii.hexlify(magic, bytes_per_sep=2)}")
        if magic[:4].hex() != "7f454c46":
            log.error("Must supply an ELF file!")
            return dict()
        else:
            offset = 4
            self.magic["ei_class"] = struct.unpack_from('<B', magic, offset)[0]
            self.magic["ei_data"] = struct.unpack_from('<B', magic, offset + 1)[0]
            self.magic["ei_version"] = struct.unpack_from('<B', magic, offset + 2)[0]
            self.magic["ei_api"] = struct.unpack_from('<B', magic, offset + 3)[0]
            # 0x01 is litte endian
            # 0x02 is big endian
            print("EI Ident values")
            if self.magic["ei_class"] == 0x2:
                print("\tARCH64")
            elif self.magic["ei_class"] == 0x1:
                print("\tAARCH32")
            if self.magic["ei_data"] == 0x1:
                print("\tLittle endian")
            elif self.magic["ei_data"] == 0x2:
                print("\tBig endian")

            return self.magic
        
    def read_elf64(self,
                 ) -> dict:
        """
        An ELF file looks like this:

        ELF Header:
        Program Header Table: Segment data for the loader
        Segments: Data dumps foe memopry
        Section Header Table: Used for linking
        Sections: Code, symbols, etc...
        Optional Data: symbol tables, relocatiopn data
        """
        # An ELF 64 packet is always 64 bytes, ELF 32 is 52 bytes
        elf_header = self.infile.read(48)

        # print(f"ELF: {binascii.hexlify(elf_header, sep=' ')}")
        elf64_hdr = dict()

        offset = 0
        elf64_hdr["e_type"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                 elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_machine"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                    elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_version"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    elf_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_hdr["e_entry"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf64_hdr["e_phoff"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf64_hdr["e_shoff"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf64_hdr["e_flags"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Word"]
        
        elf64_hdr["e_ehsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_phentsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_phnum"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_shentsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_shnum"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_shstrndx"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                     elf_header, offset)[0]

        # ELF files for linking use Sections, executables use programs, so
        # if there are program headers and no section headers, it's an
        # executable.
        if elf64_hdr["e_shnum"] == 0 and elf64_hdr["e_shentsize"] == 0 and elf64_hdr["e_phnum"] > 0:
            log.info(f"{self.mdtfile.name} is an executable ELF file")
        # print(elf64_hdr)
        return elf64_hdr
        
    def read_elf32(self,
                 ) -> dict:
        """
        An ELF file looks like this:

        ELF Header:
        Program Header Table: Segment data for the loader
        Segments: Data dumps foe memopry
        Section Header Table: Used for linking
        Sections: Code, symbols, etc...
        Optional Data: symbol tables, relocatiopn data
        """
        # An ELF 32 packet is always 32 bytes, ELF 32 is 52 bytes
        # An ELF 64 packet is always 64 bytes, ELF 32 is 52 bytes
        elf_header = self.infile.read(36)

        # print(f"ELF32: {binascii.hexlify(elf_header, sep=' ', bytes_per_sep=4)}")
        elf32_hdr = dict()

        offset = 0
        elf32_hdr["e_type"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                 elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_machine"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                    elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_version"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                    elf_header, offset)[0]
        offset += DataSizes["Elf32_Word"]

        elf32_hdr["e_entry"] = struct.unpack_from(StructTypes["Elf32_Addr"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Addr"]

        elf32_hdr["e_phoff"] = struct.unpack_from(StructTypes["Elf32_Off"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Off"]

        elf32_hdr["e_shoff"] = struct.unpack_from(StructTypes["Elf32_Off"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Off"]

        elf32_hdr["e_flags"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Word"]

        elf32_hdr["e_ehsize"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_phentsize"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_phnum"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_shentsize"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_shnum"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_shstrndx"] = struct.unpack_from(StructTypes["Elf32_Half"],
                                                     elf_header, offset)[0]

        # ELF files for linking use Sections, executables use programs, so
        # if there are program headers and no section headers, it's an
        # executable.
        if elf32_hdr["e_shnum"] == 0 and elf32_hdr["e_shentsize"] == 0 and elf32_hdr["e_phnum"] > 0:
            log.info(f"{self.mdtfile.name} is an executable ELF file")

        # print(elf32_hdr)
        return elf32_hdr

    def read_section_header64(self,
                    ) -> dict:
        """
        """
        elf64_shdr = dict()
        offset = 0
        seg_header = self.infile.read(self.elf_header["e_ehsize"])

        # log.debug(f"SEGMENT: {binascii.hexlify(seg_header, sep=' ', bytes_per_sep=8)}")
        elf64_shdr["sh_name"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_shdr["sh_type"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_shdr["sh_flags"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_shdr["sh_addr"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf64_shdr["sh_offset"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf64_shdr["sh_size"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_shdr["sh_link"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_shdr["sh_info"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_shdr["sh_addralign"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_shdr["sh_entisze"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        # offset += DataSizes["Elf64_XWord"]

        # self.dump_header(elf64_shdr)
        return elf64_shdr

    def dump_all(self):
        """
        """
        if self.mdtfile:
            print("MDT file: %s" % self.mdtfile)
        for index in range(0, self.elf_header["e_phnum"]):
            print(f"Dumping program header .b{index:02d}")
            self.dump_header(self.prog_headers[index])

        print("")
        if self.elf_header["e_shnum"] > 0:
            for index in range(0, self.elf_header["e_shnum"]):
                print(f"Dumping section header {index}")
                self.dump_header(self.seg_headers[index])
                # print(self.seg_headers[index])

    def read_program_header64(self,
                    ) -> dict:
        """
        p_type: Type of segment (e.g., PT_LOAD).
        p_flags: Memory permissions (bitmask: PF_R = read, PF_W = write, PF_X = execute).
        p_offset: Segment file offset
        p_vaddr:  Segment virtual address
        p_paddr: Segment physical address
        p_filesz: Size of disk file
        p_memsz: Segment size in memory
        p_align: Segment alignment, file & memory
        """
        elf64_phdr = dict()

        # skip to the start of the headers
        # self.infile.read(elf64_hdr["e_phoff"])

        offset = 0
        prog_header = self.infile.read(self.elf_header["e_phentsize"])

        # log.debug(f"PROGRAM: {binascii.hexlify(prog_header, sep=' ', bytes_per_sep=8)}")
        elf64_phdr["p_type"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_phdr["p_flags"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_phdr["p_offset"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf64_phdr["p_vaddr"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf64_phdr["p_paddr"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf64_phdr["p_filesz"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_phdr["p_memsz"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_phdr["p_align"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    prog_header, offset)[0]
        # offset += DataSizes["Elf64_XWord"]

        # self.dump_header(elf64_phdr)
        self.prog_headers.append(elf64_phdr)
        return elf64_phdr

    def read_program_header32(self,
                    ) -> dict:
        """
        p_type: Type of segment (e.g., PT_LOAD).
        p_flags: Memory permissions (bitmask: PF_R = read, PF_W = write, PF_X = execute).
        p_offset: Segment file offset
        p_vaddr:  Segment virtual address
        p_paddr: Segment physical address
        p_filesz: Size of disk file
        p_memsz: Segment size in memory
        p_align: Segment alignment, file & memory
        """
        elf32_phdr = dict()

        # skip to the start of the headers
        # self.infile.read(elf32_hdr["e_phoff"])

        offset = 0 # self.elf_header["e_phoff"]
        prog_header = self.infile.read(self.elf_header["e_phentsize"])

        # log.debug(f"PROGRAM: {binascii.hexlify(prog_header, sep=' ', bytes_per_sep=4)}")
        elf32_phdr["p_type"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Word"]

        elf32_phdr["p_offset"] = struct.unpack_from(StructTypes["Elf32_Off"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Off"]

        elf32_phdr["p_vaddr"] = struct.unpack_from(StructTypes["Elf32_Addr"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Addr"]

        elf32_phdr["p_paddr"] = struct.unpack_from(StructTypes["Elf32_Addr"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Addr"]

        elf32_phdr["p_filesz"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Word"]

        elf32_phdr["p_memsz"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Word"]

        elf32_phdr["p_flags"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                    prog_header, offset)[0]
        offset += DataSizes["Elf32_Word"]

        elf32_phdr["p_align"] = struct.unpack_from(StructTypes["Elf32_Word"],
                                                    prog_header, offset)[0]
        # offset += DataSizes["Elf32_Word"]

        # self.dump_header(elf32_phdr)
        self.prog_headers.append(elf32_phdr)
        return elf32_phdr

    def dump_header(self,
                    header: dict,
                    ) -> dict:
        """
        """
        for key, value in header.items():
            if key != "sh_name":
                print(f"\t{key} = {hex(value)} ({value})")
        if "p_flags" in header:
                out = ""
                for name, type in PflagPerms.items():
                    if type & header["p_flags"] > 0:
                        out += f"{name}, "
                if len(out) != 0:
                        print(f"\tpermissions are {out[:-2]}")
        if "sh_name" in header:
            for name, value in SegNames.items():
                if value == int(header["sh_name"]):
                    print(f"\tSection name is {name}")
                    continue
        if "sh_type" in header:
            if int(header["sh_type"]) <= len(ProgTypes):
                print(f"\tSection header is a {SegTypes[header["sh_type"]]}")
        if "sh_flags" in header:
            flags = str()
            if int(header["sh_flags"]) <= len(SegFlags):
                for name, mask in SegFlags.items():
                    if header["sh_flags"] & mask:
                        flags += f"{name}, "
                print(f"\tSection flags are {flags[:-2]}")

        if "p_type" in header:
            if int(header["p_type"]) <= len(ProgTypes):
                print(f"\tProgram header is a {ProgTypes[header["p_type"]]}")
            else:
                # from linux/elf.h
                # PT_GNU_EH_FRAME 0x6474e550  /* GCC .eh_frame_hdr segment */
                # PT_GNU_STACK    0x6474e551  /* Indicates stack executability */
                # PT_GNU_RELRO    0x6474e552  /* Read-only after relocation */
                # PT_LOSUNW       0x6ffffffa
                # PT_SUNWBSS      0x6ffffffa  /* Sun Specific segment */
                # PT_SUNWSTACK    0x6ffffffb  /* Stack segment */
                # PT_HISUNW       0x6fffffff
                # PT_HIOS         0x6fffffff  /* End of OS-specific */
                # PT_LOPROC       0x70000000  /* Start of processor-specific */
                # PT_HIPROC       0x7fffffff  /* End of processor-specific */
                if header["p_type"] == 0x6474e552:
                    print(f"\tProgram header is a PT_GNU_RELOC")
                else:
                    log.error(f"Unknown Type {header["p_type"]}")

    def merge_blobs(self,
                        mdtfile: str,
                        ):
        """
        Merge all the blobs into a single ELF file, which is easier
        to analyze.

        Args:
            mdtfile (str): File name pattern
        """

        path = Path(mdtfile)
        pat = f"{path.parent}/{path.stem}.b*"
        files = sorted(glob(f"{pat}"))

        if path.stem == "wpss":
            log.error(f"Can't merge WPSS files!")
            return 1

        outfile = open(f"{path.parent}/{path.stem}.elf", "wb")
        for file in files:
            log.debug(f"Merging {file} ...")
            file = open(file, "rb")
            blob = file.read()
            outfile.write(blob)

        log.info(f"Wrote {path.parent}/{path.stem}.elf")

    def get_memsize(self) -> int:
        """
        Acquire size of the memory region needed to load mdt.
        """
        min_addr = 0
        max_addr = 0
        for index in range(0, self.elf_header["e_shnum"]):
            if  self.seg_headers[index]["p_paddr"] < min_addr:
                min_addr = self.seg_headers[index]["p_paddr"]

            if  self.seg_headers[index]["p_paddr"] + self.seg_headers[index]["p_memsz"] > max_addr:
                # FIXME: this needs to be aligned to a 4K page
                max_addr = self.seg_headers[index]["p_paddr"] + self.seg_headers[index]["p_memsz"]

            return max_addr - min_addr

    def get_certs(self):
        """
        Extracts the SSL certs from the MDT file, and writes them to disk.
        The ASN.1 data starts with a 0x30 that designates a sequence,
        followed by a 0x82, that specifies the following word is the length
        in bytes of the rest of the ASN.1 data packet..
        """
        self.infile.seek(0)
        data = self.infile.read()
        index = 0
        certs = list()
        ignore = False
        for loc in data:
            # 0x30 followed by 0x82 is the ASN.1 sequence.
            if loc == 0x30:
                if data[index + 1] == 0x82:
                    log.debug(f"Found start of ASN.1 record! {hex(index)}")
                    # This is the length field in the ASN.1 sequence type,
                    # which is the entire cert.
                    length = int.from_bytes(data[index+2:index+4])
                    # log.debug(f"LENGTH: {length}")
                    cert = {"start": 0, "end": 0}
                    cert["start"] = index
                    cert["end"] = index + length + 4
                    print(cert)
                    if len(certs) == 0:
                        certs.append(cert)
                    else:
                        last = certs[-1:][0]
                        if index - last["start"] > 4:
                            certs.append(cert)
            index += 1

        for entry in certs:
            log.debug(entry)
            file = open(f"{self.mdtfile.parent/str(hex(entry['start'])[2:])}", "wb")
            file.write(data[entry["start"]:entry["end"]])
            file.close()

    def create_mdt(self,
                    mdtfile: str,
                    indir: str,
                    ):
        """
        Create and MDT file.
        """
        self.mdtfile = Path(mdtfile)
        # self.outfile = open(mdtfile, "wb")
        files = glob(f"{indir}{self.mdtfile.stem}.b*")
        log.debug(f"Found {len(files)} relevant files matching {self.mdtfile.stem}.b*")
        for file in files:
            size = os.path.getsize(file)

def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="")
    # parser.add_argument("-m", "--mdt", help="MDT file")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-d", "--dump", help="Dump All Headers")
    parser.add_argument("-s", "--stats", action="store_true", help="Get some stats on an MDT file")
    parser.add_argument("-e", "--elf", help="Merge all the program headers into an ELF file")
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    # Need at least one operation
    if len(argv) == 1:
        parser.print_help()
        quit()

    mdt = MDTTool()

    if args.elf:
        mdt.merge_blobs(args.elf)
    elif args.stats:
        mdt.read_mdt(args.mdt)
        memsize = mdt.get_memsize()
        log.info(f"Memory required {hex(memsize)}")
    elif args.stats:
        mdt.read_mdt(args.stats)
        mdt.get_certs()
    elif args.dump:
        mdt.read_mdt(args.dump)
        mdt.dump_all()

if __name__ == "__main__":
    """
    This is just a hook so this file can be run standlone during development.
    """
    main()
