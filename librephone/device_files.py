#!/usr/bin/python3

# Copyright (c) 2025 Free Software Foundation, Inc.
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

#
# Class that analyzes files
#
import argparse
import logging
import os
from sys import argv
import sys
from pathlib import Path
import re
import json
import hashlib
from progress.spinner import Spinner
from librephone.typedefs import Cputypes, Gpumodels, Devstatus, Imgtypes, Bintypes, Archtypes, Celltypes, Nettypes, Wifitypes, Filetypes, Blobtypes

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

class DeviceFiles(object):
    def __init__(self):
        """
        Returns:
            (Device): An instance of this class

        Return:
            (DeviceFiles): An instance of this class
        """
        self.files = dict()
        # FIXME: drop .pb and .dat for now, less clutter
        self.keep = (".hex", ".img", ".bin", ".fw", ".fw2")
        self.suffixes = {".jar": "JAR",
                    ".apk": "APK",
                    ".so": "LIBRARY",
                    ".sh": "BASH",
                    ".img": "IMAGE",
                    ".py": "PYTHON",
                    ".bin": "BIN",
                    ".hex": "HEX",
                    ".pb": "UNKNOWN",
                    ".fw": "FIRMWARE",
                    ".fw2": "FIRMWARE",
                    }

        # These are the values returned from using the command line
        # file program
        self.filetypes = {"TEXT": "ASCII text.*",
             "APK": "Android package.*",
             "FILESYSTEM": ".*filesystem data.*",
             "KERNEL": "Android bootimg",
             "TAR": "POSIX tar archive.*",
             "JAR": "Java archive data.*",
             "LIBRARY": "LF 64-bit LSB shared object.*",
             "XML": "XML .*",
             "PYTHON": "Python script",
             "DATA": "data",
             "EXE": "ELF 64-bit LSB pie executable.*",
             "OpenPGP": "OpenPGP secret key",
             "ARIA": "aria2 control file.*",
             "BITMAP": "Atari DEGAS Elite bitmap",
             "UNKNOWN": "PB something or other",
             "FIRMWARE": "Firmware",
             }
        # We don't care about these types now, maybe later.
        self.ignore = ["RTPSTREAM",
                       "CONFIG",
                       "ISOLATION",
                       "VIBRATION",
                       "SHADER",
                       "GRAPHIC",
                       "CAMERA",
                       "MEDIA",
                       ]

    def get_metadata(self,
                     filespec: str = None,
                     ) -> dict:
        """
        Args:
            filespec (str): The file to get info for

        Return:
            (dict): The file info
        """
        # .apk
        if filespec is None:
            return dict()

        suffix = Path(filespec).suffix
        if suffix not in self.keep:
            return dict()

        # log.debug(f"Extracting file size for {file}")
        path = f"{filespec}"
        file_size = os.stat(path).st_size
        # log.debug(f"Extracting md5sum for file {file}")
        md5sum = hashlib.md5(open(path,'rb').read()).hexdigest()

        # file_type = self.get_filetype(path)
        file_type = self.get_magic(filespec).value
        #if file_type not in self.files:
        #    self.files[file_type] = list()
        metadata = {"file": os.path.basename(filespec),
                    "size": file_size,
                    "type": file_type,
                    "md5sum": md5sum,
                    "path": os.path.dirname(path),
                    "version": 22.2, # FIXME: this shouldn't be hardcoded
                    }
        print(metadata)
        return metadata

    def get_magic(self,
                  filespec: str,
                  ):
        """
        Extract the magic number from a binary file.

        Args:
            filespec (str): The file to get info for

        """
        # Some file names have varying magic numbers, but luckily then
        # naming convention is consistent for firmware.
        nametypes = ({"pat": ".*_rtp.*hz.bin", "type": Bintypes.RTPSTREAM},
                     {"pat": ".*_cfg_.*.bin", "type": Bintypes.CONFIG},
                     {"pat": "aw8697.*.bin", "type": Bintypes.VIBRATION},
                     {"pat": "aw8695.*_rtp_.*bin", "type": Bintypes.MEDIA},
                     {"pat": "aw8624.*.bin", "type":Bintypes.AUDIOAMP},
                     {"pat": "aw87xxx.*.bin", "type":Bintypes.AUDIOAMP},
                     {"pat": "aw882.*.bin", "type":Bintypes.CODEC},
                     {"pat": "aw963xx.*.bin", "type":Bintypes.PROXIMITY},
                     {"pat": "aw8622_.*.bin", "type":Bintypes.PROXIMITY},
                     {"pat": "snap.*Binary.bin", "type": Bintypes.SHADER},
                     {"pat": "crnv21.bin", "type": Bintypes.BLUETOOTH},
                     {"pat": "cpp_firmware_v.*.fw", "type": Bintypes.WIFI_GPS_BLUETOOTH},
                     {"pat": "bm2n.*.bin", "type": Bintypes.ISOLATION},
                     {"pat": "_RTP.*.bin", "type": Bintypes.MEDIA},
                     {"pat": "shader_PROGRAM_.*.bin", "type": Bintypes.SHADER},
                     {"pat": "drv2624.*.bin", "type": Bintypes.VIBRATION},
                     {"pat": "[_.]rgb.bin", "type": Bintypes.GRAPHIC},
                     {"pat": "mibokeh.*.bin", "type": Bintypes.GRAPHIC},
                     {"pat": "misound.*.bin", "type": Bintypes.RTPSTREAM},
                     {"pat": "config.bin", "type": Bintypes.CONFIG},
                     {"pat": "[0-9]*_pre.bin", "type": Bintypes.CAMERA},
                     {"pat": "FW_FT3518_.*.bin", "type": Bintypes.TOUCHSCREEN2},
                     {"pat": "FW_FT3681_.*.bin", "type": Bintypes.TOUCHSCREEN2},
                     {"pat": "FW_GT9886_.*.bin", "type": Bintypes.TOUCHSCREEN3},
                     {"pat": "FW_NF_ILI7807S.*.bin", "type": Bintypes.TOUCHSCREEN4},
                     {"pat": "FW_S3908_.*.bin", "type": Bintypes.OLED},
                     {"pat": "FW_NF_NT36672C.*.bin", "type": Bintypes.TOUCHSCREEN5},
                     {"pat": "_S3706_.*.bin", "type": Bintypes.TOUCHSCREEN6},
                     {"pat": "_S6SY761_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY771_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY791_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY792_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "shader_PROGRAM.*.bin", "type": Bintypes.SHADER},
                     {"pat": "a630_sqe.*.bin", "type": Bintypes.GPU},
                     {"pat": "bwlan.bin", "type": Bintypes.WIFI},
                     {"pat": "bdwlan.bin", "type": Bintypes.WIFI},
                     {"pat": "ringtone_.*.bin", "type": Bintypes.MEDIA},
                     {"pat": "_rtp.bin", "type": Bintypes.MEDIA},
                     {"pat": "_[0-9]*HZ.bin", "type": Bintypes.MEDIA},
                     {"pat": "rt5514.*dsp.*.bin", "type": Bintypes.AUDIO},
                     {"pat": "score_.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "sec_s3n.*.bin", "type": Bintypes.NFC},
                     {"pat": "skinLUTs.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "st21nfc_fw.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "st54j_conf.bin", "type": Bintypes.CONFIG},
                     {"pat": "st54j_fw.bin", "type": Bintypes.NFC},
                     {"pat": "unsparse_super_empty.img", "type": Bintypes.BOOT},
                     {"pat": "usbin.bin", "type": Bintypes.USB},
                     {"pat": "xr.bin", "type": Bintypes.CAMERA},
                     {"pat": "xr.bin", "type": Bintypes.CAMERA},
                     {"pat": "yyy.bin", "type": Bintypes.CAMERA},
                     {"pat": "yyz.bin", "type": Bintypes.CAMERA},
                     {"pat": "zc.bin", "type": Bintypes.CAMERA},
                     {"pat": "a530.*.fw", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "a540.*.fw", "type": Bintypes.GPU},
                     {"pat": "a[0-9]*_gmu.bin", "type": Bintypes.GPU},
                     {"pat": "a[0-9]*]_sqe.bin", "type": Bintypes.GPU},
                     {"pat": "xusb.bin", "type": Bintypes.USB},
                     {"pat": "aoa_cldb.*bin", "type": Bintypes.WIFI},
                     {"pat": "w_dual_calibration.bin", "type": Bintypes.CAMERA},
                    )
        print(f"FIXME: {filespec}")
        for name in nametypes:
            pat = re.compile(name["pat"])
            if re.search(pat, filespec):
                return name["type"]

        # FIXME: Limit magic numbers to 4 bytes unless we can figure out
        # a better way to handle different length magic numbers.
        magic_numbers = {'png': bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
                         'AVB0': bytes([0x41, 0x56, 0x42, 0x30]),
                         'ELF64': bytes([0x7f, 0x45, 0x4c, 0x46]),
                         'MSDOS': bytes([0xeb, 0x3c, 0x90, 0x4d]),
                         'BOOT': bytes([0x41, 0x4e, 0x44, 0x52]),
                         'SD': bytes([0x73, 0x64, 0x2f, 0x0]),
                         'VNDRBOOT': bytes([0x56, 0x4e, 0x44, 0x52]),
                         'DTB': bytes([0xd7, 0xb7, 0xab, 0x1e]),
                         'FILESYSTEM': bytes([0x00, 0x00, 0x00, 0x00, 0x00]),
                         'CAMERA': bytes([0x51, 0x54, 0x49, 0x20]),
                         'FIRMWARE': bytes([0x00, 0x00, 0x00, 0xff]),
                         'FIRMWARE1': bytes([0x00, 0x00, 0x20, 0x00]),
                         'FIRMWARE2': bytes([0x03, 0x01, 0x00, 0x00]),
                         'AUDIOAMP2': bytes([0x08, 0xf9, 0x15, 0x0a]),
                         'NFC': bytes([0x13, 0x04, 0x98, 0x81]),
                         'FIRMWARE5': bytes([0x61, 0x6e, 0x63, 0x5f]),
                         'FIRMWARE6': bytes([0x69, 0x05, 0x00, 0x00]),
                         'FIRMWARE7': bytes([0x8a, 0x0d, 0x00, 0x00]),
                         'FIRMWARE8': bytes([0xb2, 0x25, 0x08, 0x00]),
                         'FIRMWARE9': bytes([0xf8, 0x88, 0x02, 0x00]),
                         'FIRMWARE10': bytes([0xff, 0xdb, 0xff, 0xe4]),
                         'SHADER': bytes([0x40, 0x87, 0x00, 0x00]),
                         'AUDIOAMP': bytes([0x57, 0x4d, 0x44, 0x52]),
                         'OLED': bytes([0x4c, 0x49, 0x4d, 0x49]),
                         'TOUCHSCREEN1': bytes([0x4c, 0x49, 0x4d, 0x49]),
                         'FINGERPRINT': bytes([0x46, 0x77, 0x55, 0x70]),
                         'TOUCHSCREEN3': bytes([0x00, 0x00, 0x09, 0x62]),
                         'TOUCHSCREEN4': bytes([0x2b, 0x47, 0x18, 0x48]),
                         'TOUCHSCREEN5': bytes([0x54, 0x46, 0x49, 0x53]),
                         'WIFI': bytes([0x03, 0x46, 0x04, 0x00]),
                         }

        # breakpoint()
        with open(filespec, "rb") as file:
            magic = file.read(4)
            for ftype, num in magic_numbers.items():
                if num == magic:
                    log.debug(f"{filespec} is {ftype}")
                    return Bintypes(ftype)
        return Bintypes.UNKNOWN

    def find_files(self,
                   indir: str,
                   ) -> dict:
        """
        Find all the proprietary files for a device.

        Args:
            indir (str): The input directory with the extracted files

        Return:
            (list): The files from the device
        """
        # spinner = Spinner('Scanning for files... ')
        for root, dirs, files in os.walk(indir):
            # spinner.next()
            base = Path(root)
            if root == indir:
                continue
            if "META-INF" in base.parts:
                continue
            # Ignore anything without vendor/build in the path.
            # base = Path(root.replace(f"{indir}/", ""))
            # print(f"FIXME: {base}")
            if len(base.parts) < 2:
                continue
            vendor = base.parts[0]
            build = base.parts[1]
            for file in files:
                if Path(file).suffix not in self.keep:
                    continue
                metadata = self.get_metadata(f"{root}/{file}")
                # ignore data files use by the blobs
                if metadata["type"] in self.ignore:
                    log.debug(f"Ignoring {metadata}")
                    continue
                #if  metadata["type"] == Bintypes.UNKNOWN:
                metadata["path"] = f"{base}"
                if metadata["type"] not in self.files:
                    self.files[metadata["type"]] = list()
                self.files[metadata["type"]].append(metadata)

        # spinner.finish()
        return self.files

    def dump(self):
        for key, val in self.files.items():
            print(f"{self.vendor}, {self.model}, {self.build}")
            print(f"\t{key}: {self.files[key]}")
            

def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Import device data into postgres")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--indir", default=".", help="Input directory")
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

    dev = DeviceFiles()
    if args.indir:
        files = dev.find_files(Path(args.indir).resolve())
        print(files)
    
if __name__ == "__main__":
    """
    This is just a hook so this file can be run standlone during development.
    """
    main()
