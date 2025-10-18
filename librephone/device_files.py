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
import magic
from progress.spinner import Spinner
import subprocess
from librephone.typedefs import Gpumodels, Devstatus, Imgtypes, Bintypes, Archtypes, Celltypes, Nettypes, Wifitypes, Filetypes, Blobtypes

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
        #if suffix not in self.keep:
        #    return dict()

        # log.debug(f"Extracting file size for {file}")
        path = f"{filespec}"
        file_size = os.stat(path).st_size
        # log.debug(f"Extracting md5sum for file {file}")
        md5sum = hashlib.md5(open(path,'rb').read()).hexdigest()

        # result = subprocess.run(
        #     [
        #         "objdump",
        #         "-a",
        #         path,
        #     ],
        #     capture_output=True,
        # )
        result = magic.from_file(path)
        print(f"MAGIC: {filespec} is {result}")
        # if str(result.stderr).find("file format not recognized") > 0:
        #     pass
        pat = "(ARM|QUALCOMM|MIPS|RISC-V)[ a-zA-Z-]*,"
        archtype = {"ARM": Archtypes.ARM,
                    "ARM aarch64": Archtypes.AARCH64,
                    "QUALCOMM DSP6": Archtypes.QUALCOMM,
                    "UNKNOWN": Archtypes.UNKNOWN,
                    "RISC-V": Archtypes.RISCV,
                    "ARM Cortex-M firmware": Archtypes.CORTEXM,
                    # FIXME need to add risc-v and mips
                    }
        out = str(result)
        match = re.search(pat, out)
        if match:
            # breakpoint()
            ftype = out[match.start():match.end() - 1]
            arch = archtype[ftype].value
            # print(f"FIXME: {filespec} is {arch}")
        else:
            arch =  Archtypes(Archtypes.UNKNOWN).value
        #print(f"FIXME: {filespec} is {archtype[ftype]}")

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
        if arch != "UNKNOWN":
            metadata["arch"] = arch
        # print(metadata)
        return metadata

    def get_magic(self,
                  filespec: str,
                  ):
        """
        Identify the file type by examining the filename where it's
        consistent, and if not recognized, extract the possible magic
        number from the binary file.

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
                     {"pat": "a650_.*.bin", "type":Bintypes.AUDIO},
                     {"pat": "a650_.*.fw", "type":Bintypes.AUDIO},
                     {"pat": "a660_.*.fw", "type":Bintypes.AUDIO},
                     {"pat": "a660_.*.bin", "type":Bintypes.AUDIO},
                     {"pat": "adsp.[0-9]*", "type":Bintypes.AUDIO},
                     {"pat": "adsp.b[a-z]*", "type":Bintypes.AUDIO},
                     {"pat": "cdsp.b[0-9]*", "type":Bintypes.COMPUTE},
                     {"pat": "cdsp.[a-z][a-z][a-z]", "type":Bintypes.COMPUTE},
                     {"pat": "sn100u.bin", "type":Bintypes.AUDIO},
                     {"pat": "cs35l41-dsp.*.bin", "type":Bintypes.AUDIOAMP},
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
                     {"pat": "iris.*.fw", "type": Bintypes.CAMERA},
                     {"pat": "CFR_OnePlus.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "_FT3518_.*.bin", "type": Bintypes.TOUCHSCREEN2},
                     {"pat": "_FT3681_.*.bin", "type": Bintypes.TOUCHSCREEN2},
                     {"pat": "_FT3681_.*.bin", "type": Bintypes.TOUCHSCREEN2},
                     {"pat": "_FT3518_SAMSUNG.*img", "type": Bintypes.TOUCHSCREEN3},
                     {"pat": "_NF_ILI7807S.*.bin", "type": Bintypes.TOUCHSCREEN4},
                     {"pat": "_S3908_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S3908_.*.img", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "focaltech-[a-z]*-ft8756.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_NF_NT36672C.*.bin", "type": Bintypes.TOUCHSCREEN5},
                     {"pat": "_NF_NT36672C.*.img", "type": Bintypes.TOUCHSCREEN5},
                     {"pat": "_S3706_.*.bin", "type": Bintypes.TOUCHSCREEN6},
                     {"pat": "_S6SY761_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY761_.*.img", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY771_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY771_.*.img", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY791_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY791_.*.img", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY792_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_S6SY792_.*.img", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "anc_.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "_GT98[0-9]*_SAMSUNG.*.img", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "goodix_firmware_ak.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "cs40l26.*.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "aoc.bin", "type": Bintypes.TOUCHSCREEN},
                     {"pat": "shader_PROGRAM.*.bin", "type": Bintypes.SHADER},
                     {"pat": "a630_sqe.*.bin", "type": Bintypes.GPU},
                     {"pat": "a630_sqe.*.fw", "type": Bintypes.GPU},
                     {"pat": "mali_csffw-.*.bin", "type": Bintypes.GPU},
                     {"pat": "bdwlan.*.bin", "type": Bintypes.WIFI},
                     {"pat": "bdwlan.*.e[0-9][0-9]", "type": Bintypes.WIFI},
                     {"pat": "bm2n*.bin", "type": Bintypes.WIFI},
                     {"pat": "wineview.b[0-9][0-9]", "type": Bintypes.DRM},
                     {"pat": "fingerpr.b[0-9][0-9]", "type": Bintypes.FINGERPRINT},
                     {"pat": "modem.b[0-9][0-9]", "type": Bintypes.CELL},
                     {"pat": "ringtone_.*.bin", "type": Bintypes.MEDIA},
                     {"pat": "_rtp.bin", "type": Bintypes.MEDIA},
                     {"pat": "st54l_.*bin", "type": Bintypes.NFC},
                     {"pat": "_[0-9]*HZ.bin", "type": Bintypes.MEDIA},
                     {"pat": "rt5514.*dsp.*.bin", "type": Bintypes.AUDIO},
                     {"pat": "score_.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "sec_s3n.*.bin", "type": Bintypes.NFC},
                     {"pat": "skinLUTs.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "st21nfc_fw.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "unified_kb.*.bin", "type": Bintypes.CAMERA},
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
                     {"pat": "amss20.bin", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "m3.bin", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "bdwlan.*", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "regdb.bin", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "fw_bcmdhd.bin", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "htnv[0-9]*.bin", "type": Bintypes.BLUETOOTH},
                     {"pat": "htbtfw[0-9]*.bin", "type": Bintypes.BLUETOOTH},
                     {"pat": "a540.*.fw", "type": Bintypes.GPU},
                     {"pat": "a[0-9]*_gmu.bin", "type": Bintypes.GPU},
                     {"pat": "a[0-9]*]_sqe.bin", "type": Bintypes.GPU},
                     {"pat": "xusb.bin", "type": Bintypes.USB},
                     {"pat": "aoa_cldb.*bin", "type": Bintypes.WIFI},
                     {"pat": "MICRONMT128GB.*.img", "type": Bintypes.STORAGE},
                     {"pat": "KIOXIATH.*.img", "type": Bintypes.STORAGE},
                     {"pat": "SAMSUNGKLUDG4UHGC-.*.img", "type": Bintypes.STORAGE},
                     {"pat": "w_dual_calibration.bin", "type": Bintypes.CAMERA},
                     {"pat": "esim-full.*.img", "type": Bintypes.ESIM},
                     {"pat": "edgetpu-rio.fw", "type": Bintypes.AI},
                     {"pat": "gxp-callisto.fw", "type": Bintypes.AI},
                     {"pat": "ellc.bin", "type": Bintypes.CAMERA},
                     {"pat": "com.qti.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "FW_NF_ILI7807S_.*img", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "filter.bin", "type": Bintypes.CAMERA},
                     {"pat": "[E[]ye_.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "[Ff]ac[ei].*.bin", "type": Bintypes.CAMERA},
                     {"pat": "FW_NF_ILI7807S.*.img", "type": Bintypes.WIFI_BLUETOOTH},
                     {"pat": "dual.*.bin", "type": Bintypes.CAMERA},
                     {"pat": "oplus_vooc_fw_.*.bin", "type": Bintypes.FASTCHG},
                     {"pat": "effect_[0-9].bin", "type": Bintypes.VIBRATION},
                     {"pat": "w_dual_calibration.bin", "type": Bintypes.CAMERA},
                    )
        # print(f"FIXME: {filespec}")
        for name in nametypes:
            pat = re.compile(name["pat"])
            if re.search(pat, filespec):
                return name["type"]

        # These are the top level blobs from the radio directory, and need to be
        # direct name match.
        name = os.path.basename(filespec)
        radioblobs = {"xbl.img": Bintypes.UEFIBOOT,
                      "abl.img": Bintypes.UEFIBOOT,
                      "boot.img": Bintypes.BOOT,
                      "init_boot.img": Bintypes.BOOT,
                      "recovery.img": Bintypes.BOOT,
                      "dtbo.img": Bintypes.DTB,
                      "bl1.img": Bintypes.BOOT,
                      "bl31.img": Bintypes.BOOT,
                      "gcf.img": Bintypes.UNKNOWN,
                      "gsa.img": Bintypes.SECURITY,
                      "pbl.img": Bintypes.UNKNOWN,
                      "ldfw.img": Bintypes.UNKNOWN,
                      "vbmeta.img": Bintypes.AVB,
                      "vbmeta_system.img": Bintypes.AVB,
                      "vbmeta_boot.img": Bintypes.AVB,
                      "pvmfw.img": Bintypes.SECURITY,
                      "tzsw.img": Bintypes.BOOT,
                      "tz.img": Bintypes.BOOT,
                      "gsa_bl1.img": Bintypes.SECURITY,
                      "modem.img": Bintypes.CELL_WIFI_GPS_BLUETOOTH,
                      "bluetooth.img": Bintypes.BLUETOOTH,
                      "studybk.img": Bintypes.UNKNOWN,
                      "uefisecapp.img": Bintypes.UNKNOWN,
                      "cpucp.img": Bintypes.UNKNOWN,
                      "keymaster.img": Bintypes.SECURITY,
                      "featenabler.img": Bintypes.UNKNOWN,
                      "devcfg.img": Bintypes.UNKNOWN,
                      "aop.img": Bintypes.UNKNOWN,
                      "aoc.img": Bintypes.UNKNOWN,
                      "hyp.img": Bintypes.SECUREBOOT,
                      "devcfg.img": Bintypes.UNKNOWN,
                      "multiimgoem.img": Bintypes.UNKNOWN,
                      "imagefv.img": Bintypes.GRAPHIC,
                      "logo.img": Bintypes.GRAPHIC,
                      }

        # breakpoint()
        if name in radioblobs:
            return radioblobs[name]

        log.debug(f"No type found for {filespec}, checking magic number")

        # FIXME: Limit magic numbers to 4 bytes unless we can figure out
        # a better way to handle different length magic numbers.
        magic_numbers = {'png': bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
                         'AVB': bytes([0x41, 0x56, 0x42, 0x30]),
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
                         # 'AUDIOAMP2': bytes([0x08, 0xf9, 0x15, 0x0a]),
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
                         'FASTCHG': bytes([0x46, 0x77, 0x55, 0x70]),
                         'TOUCHSCREEN3': bytes([0x00, 0x00, 0x09, 0x62]),
                         'TOUCHSCREEN4': bytes([0x2b, 0x47, 0x18, 0x48]),
                         'TOUCHSCREEN5': bytes([0x54, 0x46, 0x49, 0x53]),
                         'WIFI': bytes([0x03, 0x46, 0x04, 0x00]),
                         }

        # breakpoint()
        # foo = magic.from_file(filespec)
        with open(filespec, "rb") as file:
            magicnum = file.read(4)
            for ftype, num in magic_numbers.items():
                if num == magicnum:
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
            if len(base.parts) < 2:
                continue
            vendor = base.parts[0]
            build = base.parts[1]
            pat = re.compile("[a-z0-9*].[a-z][0-9][0-9]")
            skip = [".pb", ".dat"]
            for file in files:
                if Path(file).suffix in skip:
                    continue
                # if Path(file).suffix not in self.keep:
                #    if not re.match(pat, file):
                #        continue
                metadata = self.get_metadata(f"{root}/{file}")
                # ignore data files use by the blobs
                if len(metadata) == 0 or metadata["type"] in self.ignore:
                    log.debug(f"Ignoring {file}")
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
