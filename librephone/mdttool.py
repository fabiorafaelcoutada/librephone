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


P_Types = ["PT_NULL", "PT_LOAD", "PT_DYNAMIC", "PT_INTERP", "PT_NOTE", "PT_SHLIB", "PT_PHDR"]

# This program does multiple reads of the same file, so if you screw up the size of a
# data field, all the following ones will be wrong.

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
        self.seg_headers = list()
        
    def read_mdt(self,
                 mdtfile: str = None,
                 ):
        """
        """
        if mdtfile:
            self.mdtfile = Path(mdtfile)
            output = mdtfile.replace(".mdt", ".elf")
            if os.path.exists(output):
                os.remove(output)
            self.outfile = open(output, "ab")
            self.infile = open(mdtfile, "rb")
        elif self.mdtfile:
            mdt = open(self.mdtfile, "rb")

        self.magic = self.infile.read(16)
        self.read_magic(self.magic)
        # self.outfile.write(self.magic)

        # The offsets are from the elf.h header file
        elf_header = self.infile.read(64)
        self.magic + elf_header
        self.elf_header = self.read_elf(elf_header)
        # self.outfile.write(elf_header)

        # print("Dumping ELF Header")
        # self.dump_header(self.elf_header)
        # print("------------------------------")
        for i in range(0, self.elf_header["e_shnum"]):
            data = self.read_header(self.elf_header["e_shentsize"])
            # print("Dumping segment header")
            # self.dump_header(data)
            self.seg_headers.append(data)

    def read_magic(self,
                   magic: byes,
                   ):
        """
        """
        # print(f"MAGIC: {binascii.hexlify(magic)}")
        if magic[:4].hex() != "7f454c46":
            log.error("Must supply an ELF file!")
            return 1
        else:
            # 0x01 is litte endian last byte
            # 0x02 is big endian last byte
            return 0
        
    def read_elf(self,
                 elf_header: bytes,
                 ) -> dict:
        """
        """
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
        offset += DataSizes["Elf32_Word"]
        
        elf64_hdr["e_ehsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_shentsize"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                      elf_header, offset)[0]
        offset += DataSizes["Elf64_Half"]

        elf64_hdr["e_shnum"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                  elf_header, offset)[0]
        offset += DataSizes["Elf32_Half"]

        elf64_hdr["e_shstrndx"] = struct.unpack_from(StructTypes["Elf64_Half"],
                                                     elf_header, offset)[0]

        return elf64_hdr
        
    def read_header(self,
                    hdr_size: int,
                    ) -> dict:
        """
        """
        elf64_phdr = dict()
        offset = 0
        seg_header = self.infile.read(hdr_size)

        # log.debug(f"SEGMENT: {binascii.hexlify(seg_header, sep=' ', bytes_per_sep=8)}")
        elf64_phdr["p_type"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_phdr["p_flags"] = struct.unpack_from(StructTypes["Elf64_Word"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Word"]

        elf64_phdr["p_offset"] = struct.unpack_from(StructTypes["Elf64_Off"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Off"]

        elf64_phdr["p_vaddr"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf64_phdr["p_paddr"] = struct.unpack_from(StructTypes["Elf64_Addr"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_Addr"]

        elf64_phdr["p_filesz"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_phdr["p_memsz"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        offset += DataSizes["Elf64_XWord"]

        elf64_phdr["p_align"] = struct.unpack_from(StructTypes["Elf64_XWord"],
                                                    seg_header, offset)[0]
        # offset += DataSizes["Elf64_XWord"]

        # self.dump_header(elf64_phdr)
        return elf64_phdr

    def dump_all(self):
        """
        """
        print("Dumping ELF header")
        self.dump_header(self.elf_header)
        print("-------------------------")
        for index in range(0, self.elf_header["e_shnum"]):
            print(f"Dumping program header {index}")
            self.dump_header(self.seg_headers[index])

    def dump_header(self,
                    header: dict,
                    ) -> dict:
        """
        """
        # if self.mdtfile:
        #    print("MDT file: %s" % self.mdtfile)
        for key, value in header.items():
            print(f"\t{key} = {hex(value)} ({value})")
        if "p_type" in header:
            foo = header["p_type"]
            # P_Types[h)eader["p_type"]]

    def merge_blobs(self,
                        pattern: str,
                        indir: str = '.',
                        outdir: str = 'out',
                        ):
        """
        Merge all the blobs into a single ELF file, which is easier
        to analyze.

        Args:
            pattern (str):
            indir (str):
            outdir (str):
        """

        # if not self.elf_header:
        #     mdtfile = f"{indir}{pattern}")
        #     self.read_mdt()

        pat = f"{indir}/{pattern}.b*"
        files = sorted(glob(f"{pat}"))

        if not os.path.exists(outdir):
            os.mkdir(outdir)
        outfile = open(f"{outdir}/{pattern}.elf", "wb")
        for file in files:
            log.debug(f"Merging {file} ...")
            file = open(file, "rb")
            blob = file.read()
            outfile.write(blob)

        log.info(f"{outdir}/{pattern}.elf")

        # comments on the net claim no file size shouldn't be
        # part of the output file, but it turns out that's the
        # ELF header.
        # for index in range(0, self.elf_header["e_shnum"]):
        #     if self.seg_headers[index]["p_filesz"] == 0:
        #         print(f"{base}{index:02d} has no file size")
        #         # continue
        #     log.debug(f"Merging {base}{index:02d}...")
        #     file = open(f"{base}{index:02d}", "rb")
        #     blob = file.read()
        #     self.outfile.write(blob)
        # log.info(f"Wrote {base}{index:02d}")

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
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-m", "--mdt", help="MDT file")
    parser.add_argument("-d", "--dump", action="store_true", help="Dump All Headers")
    parser.add_argument("-i", "--indir", help="Create  an MDT file for a directory")
    parser.add_argument("-o", "--outdir", default="out", help="Output directory")
    parser.add_argument("-s", "--stats", help="Get some stats on an MDT file")
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
        mdt.merge_blobs(args.elf, args.indir, args.outdir)
    elif args.stats:
        mdt.read_mdt(args.mdt)
        memsize = mdt.get_memsize()
        log.info(f"Memory required {hex(memsize)}")
    elif args.stats:
        mdt.read_mdt(args.mdt)
        mdt.get_certs()
    elif args.dump:
        mdt.read_mdt(args.mdt)
        mdt.dump_all()

    if args.indir:
        # mdt.create_mdt(args.indir)
        pass

if __name__ == "__main__":
    """
    This is just a hook so this file can be run standlone during development.
    """
    main()
