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

    
# elf321_phdr = {
#     "p_type": None,
#     "p_offset": None,
#     "p_vaddr": None,
#     "p_paddr": None,
#     "p_filesz": None,
#     "p_memsz": None,
#     "p_flags": None,
#     "p_align": None,
# }

# elf32_hdr = {
#     "e_ident": None,
#     "e_type": None,
#     "e_machine": None,
#     "e_version": None,
#     "e_entry": None,
#     "e_phoff": None,
#     "e_shoff": None,
#     "e_flags": None,
#     "e_ehsize": None,
#     "e_phentsize": None,
#     "e_phnum": None,
#     "e_shentsize": None,
#     "e_shnum": None,
#     "e_shstrndx": None,
# }

class MDTTool(object):
    def __init__(self,
                 mdtfile: str() = None,
                 ):
        """
        Returns:
            (MDTool): An instance of this class

        Args:
            mdtfile (str): The MDT file
        """
        if mdtfile:
            self.mdtfile = Path(mdtfile)
            output = mdtfile.replace(".mdt", ".elf")
            self.outfile = open(output, "w")
            self.infile = open(mdtfile, "rb")
        else:
            self.mdtfile = None
            self.outfile = None
            self.infile = None

        self.elf_header_size = 64
        self.magic_size = 0x10
        self.this_hdr_size = 0
        self.hdr_count = 0
        self.hdr_size = 0
        
    def read_mdt(self,
                 mdtfile = None,
                 ):
        """
        """
        if mdtfile:
            self.infile = open(mdtfile, "rb")
        elif self.mdtfile:
            mdt = open(self.mdtfile, "rb")

        magic = self.infile.read(self.magic_size)
        self.read_magic(magic)

        # The offsets are from the elf.h header file
        elf_header = self.infile.read(self.elf_header_size)
        self.read_elf(elf_header)

        for i in range(0, self.hdr_count):
            self.read_header()

    def read_magic(self,
                   magic: byes,
                   ):
        """
        """
        print(f"MAGIC: {binascii.hexlify(magic)}")
        if magic[:4].hex() != "7f454c46":
            log.error("Must supply an ELF file!")
            return 1
        else:
            return 0
        
    def read_elf(self,
                 elf_header: bytes,
                 ):
        """
        """
        print(f"ELF: {binascii.hexlify(elf_header, sep=' ')}")
        elf32_hdr = dict()

        # EI_NIDENT = 16 (0x10)hex(offset)}
        # the first field is the e_ident, which is a string
        # elf32_hdr["e_ident"] = struct.unpack_from("<s", elf_header, 0)[0]
        
        offset = 0
        elf32_hdr["e_type"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                 elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]
        
        elf32_hdr["e_machine"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                    elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf32_hdr["e_version"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    elf_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf32_hdr["e_entry"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf32_hdr["e_phoff"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf32_hdr["e_shoff"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf32_hdr["e_flags"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Word"]
        
        elf32_hdr["e_ehsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf32_hdr["e_shentsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf32_hdr["e_shnum"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf32_hdr["e_shstrndx"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                     elf_header, offset)[0]

        print(elf32_hdr)

        return elf32_hdr
        
    def read_header(self,
                    ):
        """
        """
        # log.info(f"Processing {filespec}")
        elf321_phdr = dict()        
        header = self.infile.read(self.hdr_size)
        print(f"{binascii.hexlify(header)}")
        elf321_phdr["p_type"] = struct.unpack("<I", header[:4])[0]
        print(f"p_type: {hex(elf321_phdr["p_type"])}")

        elf321_phdr["p_offset"] = struct.unpack("<I", header[4:8])[0]
        print(f"p_offset: {hex(elf321_phdr["p_offset"])}")

        elf321_phdr["p_vaddr"] = struct.unpack("<I", header[8:12])[0]
        print(f"p_vaddr: {hex(elf321_phdr["p_vaddr"])}")

        elf321_phdr["p_paddr"] = struct.unpack("<I", header[12:16])[0]
        print(f"p_paddr: {hex(elf321_phdr["p_paddr"])}")

        elf321_phdr["p_filesz"] = struct.unpack("<I", header[16:20])[0]
        print(f"p_filesz: {hex(elf321_phdr["p_filesz"])}")

        elf321_phdr["p_memsiz"] = struct.unpack("<I", header[20:24])[0]
        print(f"p_memsiz: {hex(elf321_phdr["p_memsiz"])}")

        elf321_phdr["p_flags"] = struct.unpack("<I", header[24:28])[0]
        print(f"p_flags: {hex(elf321_phdr["p_flags"])}")

        elf321_phdr["p_align"] = struct.unpack("<I", header[28:32])[0]
        print(f"p_align: {hex(elf321_phdr["p_align"])}")

        return elf321_phdr

def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-m", "--mdt", default=".", help="MDT file")
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

    mdt = MDTTool(args.mdt)
    mdt.read_mdt()

if __name__ == "__main__":
    """
    This is just a hook so this file can be run standlone during development.
    """
    main()
