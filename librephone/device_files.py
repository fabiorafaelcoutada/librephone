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
import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from sys import argv

import magic

import librephone as pt
from librephone.typedefs import (
    Archtypes,
    Bintypes,
)

rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

class DeviceFiles(object):
    # Optimization: Pre-compile regexes and define constants at class level
    # to avoid recreation on every function call.
    NAMETYPES = [
        (re.compile(".*_rtp.*hz.bin"), Bintypes.RTPSTREAM),
        (re.compile(".*_cfg_.*.bin"), Bintypes.CONFIG),
        (re.compile("aw8697.*.bin"), Bintypes.VIBRATION),
        (re.compile("aw8695.*_rtp_.*bin"), Bintypes.MEDIA),
        (re.compile("aw8624.*.bin"), Bintypes.AUDIOAMP),
        (re.compile("aw87xxx.*.bin"), Bintypes.AUDIOAMP),
        (re.compile("a650_.*.bin"), Bintypes.AUDIO),
        (re.compile("a650_.*.fw"), Bintypes.AUDIO),
        (re.compile("a660_.*.fw"), Bintypes.AUDIO),
        (re.compile("a660_.*.bin"), Bintypes.AUDIO),
        (re.compile("adsp.[0-9]*"), Bintypes.MODEM),
        (re.compile("adsp.b[a-z]*"), Bintypes.MODEM),
        (re.compile("cdsp.b[0-9]*"), Bintypes.COMPUTE),
        (re.compile("cdsp.[a-z][a-z][a-z]"), Bintypes.COMPUTE),
        (re.compile("sn100u.bin"), Bintypes.AUDIO),
        (re.compile("cs35l41-dsp.*.bin"), Bintypes.AUDIOAMP),
        (re.compile("aw882.*.bin"), Bintypes.CODEC),
        (re.compile("aw963xx.*.bin"), Bintypes.PROXIMITY),
        (re.compile("aw8622_.*.bin"), Bintypes.PROXIMITY),
        (re.compile("snap.*Binary.bin"), Bintypes.SHADER),
        (re.compile("crnv21.bin"), Bintypes.BLUETOOTH),
        (re.compile("cpp_firmware_v.*.fw"), Bintypes.WIFI_GPS_BLUETOOTH),
        (re.compile("bm2n.*.bin"), Bintypes.ISOLATION),
        (re.compile("_RTP.*.bin"), Bintypes.MEDIA),
        (re.compile("qdsp6m.qdb"), Bintypes.MEDIA),
        (re.compile("shader_PROGRAM_.*.bin"), Bintypes.SHADER),
        (re.compile("drv2624.*.bin"), Bintypes.VIBRATION),
        (re.compile("[_.]rgb.bin"), Bintypes.GRAPHIC),
        (re.compile("mibokeh.*.bin"), Bintypes.GRAPHIC),
        (re.compile("misound.*.bin"), Bintypes.RTPSTREAM),
        (re.compile("config.bin"), Bintypes.CONFIG),
        (re.compile("[0-9]*_pre.bin"), Bintypes.CAMERA),
        (re.compile("iris.*.fw"), Bintypes.CAMERA),
        (re.compile("fw_ipa_gsi.*elf"), Bintypes.CERT),
        (re.compile("wpss.b[0-9]"), Bintypes.BOOT),
        (re.compile("sp_license.b[0-9]*"), Bintypes.CERT),
        (re.compile("cpusys_vm.b[0-9]*"), Bintypes.SECURITY),
        (re.compile("ipa_fws.b[0-9]*"), Bintypes.CELL),
        (re.compile("soter[0-9]*"), Bintypes.FINGERPRINT),
        (re.compile("smplap[0-9]*.b[0-9]*"), Bintypes.SECURITY),
        (re.compile(".*\\.mbn"), Bintypes.SECURITY),
        (re.compile("CFR_OnePlus.*.bin"), Bintypes.CAMERA),
        (re.compile("_FT3518_.*.bin"), Bintypes.TOUCHSCREEN2),
        (re.compile("_FT3681_.*.bin"), Bintypes.TOUCHSCREEN2),
        (re.compile("_FT3681_.*.bin"), Bintypes.TOUCHSCREEN2),
        (re.compile("_FT3518_SAMSUNG.*img"), Bintypes.TOUCHSCREEN3),
        (re.compile("_NF_ILI7807S.*.bin"), Bintypes.TOUCHSCREEN4),
        (re.compile("_S3908_.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_S3908_.*.img"), Bintypes.TOUCHSCREEN),
        (re.compile("focaltech-[a-z]*-ft8756.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_NF_NT36672C.*.bin"), Bintypes.TOUCHSCREEN5),
        (re.compile("_NF_NT36672C.*.img"), Bintypes.TOUCHSCREEN5),
        (re.compile("_S3706_.*.bin"), Bintypes.TOUCHSCREEN6),
        (re.compile("_S6SY761_.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY761_.*.img"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY771_.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY771_.*.img"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY791_.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY791_.*.img"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY792_.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_S6SY792_.*.img"), Bintypes.TOUCHSCREEN),
        (re.compile("anc_.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("_GT98[0-9]*_SAMSUNG.*.img"), Bintypes.TOUCHSCREEN),
        (re.compile("goodix_firmware_ak.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("cs40l26.*.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("aoc.bin"), Bintypes.TOUCHSCREEN),
        (re.compile("shader_PROGRAM.*.bin"), Bintypes.SHADER),
        (re.compile("a630_sqe.*.bin"), Bintypes.GPU),
        (re.compile("a630_sqe.*.fw"), Bintypes.GPU),
        (re.compile("mali_csffw-.*.bin"), Bintypes.GPU),
        (re.compile("bdwlan.*.bin"), Bintypes.WIFI),
        (re.compile("bdwlan.*.e[0-9][0-9]"), Bintypes.WIFI),
        (re.compile("bm2n[0-9][0-9].bin"), Bintypes.WIFI),
        (re.compile("wineview.b[0-9][0-9]"), Bintypes.DRM),
        (re.compile("fingerpr.b[0-9][0-9]"), Bintypes.FINGERPRINT),
        (re.compile("modem.b[0-9][0-9]"), Bintypes.CELL),
        (re.compile("ringtone_.*.bin"), Bintypes.MEDIA),
        (re.compile("_rtp.bin"), Bintypes.MEDIA),
        (re.compile("st54l_.*bin"), Bintypes.NFC),
        (re.compile("_[0-9]*HZ.bin"), Bintypes.MEDIA),
        (re.compile("rt5514.*dsp.*.bin"), Bintypes.AUDIO),
        (re.compile("score_.*.bin"), Bintypes.CAMERA),
        (re.compile("sec_s3n.*.bin"), Bintypes.NFC),
        (re.compile("skinLUTs.*.bin"), Bintypes.CAMERA),
        (re.compile("st21nfc_fw.*.bin"), Bintypes.CAMERA),
        (re.compile("unified_kb.*.bin"), Bintypes.CAMERA),
        (re.compile("st54j_conf.bin"), Bintypes.CONFIG),
        (re.compile("st54j_fw.bin"), Bintypes.NFC),
        (re.compile("unsparse_super_empty.img"), Bintypes.BOOT),
        (re.compile("usbin.bin"), Bintypes.USB),
        (re.compile("xr.bin"), Bintypes.CAMERA),
        (re.compile("xr.bin"), Bintypes.CAMERA),
        (re.compile("yyy.bin"), Bintypes.CAMERA),
        (re.compile("yyz.bin"), Bintypes.CAMERA),
        (re.compile("zc.bin"), Bintypes.CAMERA),
        (re.compile("a530.*.fw"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("amss20.bin"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("m3.bin"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("bdwlan.*"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("regdb.bin"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("fw_bcmdhd.bin"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("htnv[0-9]*.bin"), Bintypes.BLUETOOTH),
        (re.compile("htbtfw[0-9]*.bin"), Bintypes.BLUETOOTH),
        (re.compile("a540.*.fw"), Bintypes.GPU),
        (re.compile("a[0-9]*_gmu.bin"), Bintypes.GPU),
        (re.compile("a[0-9]*]_sqe.bin"), Bintypes.GPU),
        (re.compile("xusb.bin"), Bintypes.USB),
        (re.compile("aoa_cldb.*bin"), Bintypes.WIFI),
        (re.compile("MICRONMT128GB.*.img"), Bintypes.STORAGE),
        (re.compile("KIOXIATH.*.img"), Bintypes.STORAGE),
        (re.compile("SAMSUNGKLUDG4UHGC-.*.img"), Bintypes.STORAGE),
        (re.compile("w_dual_calibration.bin"), Bintypes.CAMERA),
        (re.compile("esim-full.*.img"), Bintypes.ESIM),
        (re.compile("edgetpu-rio.fw"), Bintypes.AI),
        (re.compile("gxp-callisto.fw"), Bintypes.AI),
        (re.compile("ellc.bin"), Bintypes.CAMERA),
        (re.compile("com.qti.*.bin"), Bintypes.CAMERA),
        (re.compile("FW_NF_ILI7807S_.*img"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("filter.bin"), Bintypes.CAMERA),
        (re.compile("[E[]ye_.*.bin"), Bintypes.CAMERA),
        (re.compile("[Ff]ac[ei].*.bin"), Bintypes.CAMERA),
        (re.compile("FW_NF_ILI7807S.*.img"), Bintypes.WIFI_BLUETOOTH),
        (re.compile("hdcp.*.b[0-9]*"), Bintypes.DRM),
        (re.compile("dual.*.bin"), Bintypes.CAMERA),
        (re.compile("oplus_vooc_fw_.*.bin"), Bintypes.FASTCHG),
        (re.compile("effect_[0-9].bin"), Bintypes.VIBRATION),
        (re.compile("w_dual_calibration.bin"), Bintypes.CAMERA),
        (re.compile(".*kernelcache.*"), Bintypes.BOOT),
        (re.compile(".*dyld_shared_cache.*"), Bintypes.MACH_O),
        (re.compile(".*.plist"), Bintypes.CONFIG),
    ]

    RADIOBLOBS = {
        "xbl.img": Bintypes.UEFIBOOT,
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
        "multiimgoem.img": Bintypes.UNKNOWN,
        "imagefv.img": Bintypes.GRAPHIC,
        "logo.img": Bintypes.GRAPHIC,
    }

    # FIXME: Limit magic numbers to 4 bytes unless we can figure out
    # a better way to handle different length magic numbers.
    # Updated to list of tuples to support multiple magic numbers per type and variable lengths.
    MAGIC_NUMBERS = [
        ("GRAPHIC", bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])), # png
        ("AVB", bytes([0x41, 0x56, 0x42, 0x30])),
        ("ELF64", bytes([0x7f, 0x45, 0x4c, 0x46])),
        ("MSDOS", bytes([0xeb, 0x3c, 0x90, 0x4d])),
        ("BOOT", bytes([0x41, 0x4e, 0x44, 0x52])),
        ("SD", bytes([0x73, 0x64, 0x2f, 0x0])),
        ("VNDRBOOT", bytes([0x56, 0x4e, 0x44, 0x52])),
        ("DTB", bytes([0xd7, 0xb7, 0xab, 0x1e])),
        ("FILESYSTEM", bytes([0x00, 0x00, 0x00, 0x00, 0x00])),
        ("CAMERA", bytes([0x51, 0x54, 0x49, 0x20])),
        ("FIRMWARE", bytes([0x00, 0x00, 0x00, 0xff])),
        ("FIRMWARE1", bytes([0x00, 0x00, 0x20, 0x00])),
        ("FIRMWARE2", bytes([0x03, 0x01, 0x00, 0x00])),
        # 'AUDIOAMP2': bytes([0x08, 0xf9, 0x15, 0x0a]),
        ("NFC", bytes([0x13, 0x04, 0x98, 0x81])),
        ("FIRMWARE5", bytes([0x61, 0x6e, 0x63, 0x5f])),
        ("FIRMWARE6", bytes([0x69, 0x05, 0x00, 0x00])),
        ("FIRMWARE7", bytes([0x8a, 0x0d, 0x00, 0x00])),
        ("FIRMWARE8", bytes([0xb2, 0x25, 0x08, 0x00])),
        ("FIRMWARE9", bytes([0xf8, 0x88, 0x02, 0x00])),
        ("FIRMWARE10", bytes([0xff, 0xdb, 0xff, 0xe4])),
        ("SHADER", bytes([0x40, 0x87, 0x00, 0x00])),
        ("AUDIOAMP", bytes([0x57, 0x4d, 0x44, 0x52])),
        ("OLED", bytes([0x4c, 0x49, 0x4d, 0x49])),
        ("TOUCHSCREEN1", bytes([0x4c, 0x49, 0x4d, 0x49])),
        ("FASTCHG", bytes([0x46, 0x77, 0x55, 0x70])),
        ("TOUCHSCREEN3", bytes([0x00, 0x00, 0x09, 0x62])),
        ("TOUCHSCREEN4", bytes([0x2b, 0x47, 0x18, 0x48])),
        ("TOUCHSCREEN5", bytes([0x54, 0x46, 0x49, 0x53])),
        ("WIFI", bytes([0x03, 0x46, 0x04, 0x00])),
        ("MACH_O", bytes([0xfe, 0xed, 0xfa, 0xce])), # 32-bit BE
        ("MACH_O", bytes([0xce, 0xfa, 0xed, 0xfe])), # 32-bit LE
        ("MACH_O", bytes([0xfe, 0xed, 0xfa, 0xcf])), # 64-bit BE
        ("MACH_O", bytes([0xcf, 0xfa, 0xed, 0xfe])), # 64-bit LE
        ("MACH_O", bytes([0xca, 0xfe, 0xba, 0xbe])), # Fat BE
        ("MACH_O", bytes([0xbe, 0xba, 0xfe, 0xca])), # Fat LE
    ]

    def __init__(self):
        """Returns:
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
        """Args:
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
        try:
            file_size = os.stat(path).st_size
        except FileNotFoundError:
             return dict()

        # log.debug(f"Extracting md5sum for file {file}")
        try:
            md5sum = hashlib.md5(open(path,"rb").read()).hexdigest()
        except Exception:
             md5sum = "unknown"

        # result = subprocess.run(
        #     [
        #         "objdump",
        #         "-a",
        #         path,
        #     ],
        #     capture_output=True,
        # )
        try:
            result = magic.from_file(path)
        except Exception:
            result = "unknown"

        # print(f"MAGIC: {filespec} is {result}")
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
                    "version": 23.0, # FIXME: this shouldn't be hardcoded
                    }
        if arch != "UNKNOWN":
            metadata["arch"] = arch
        # print(metadata)
        return metadata

    def get_magic(self,
                  filespec: str,
                  ):
        """Identify the file type by examining the filename where it's
        consistent, and if not recognized, extract the possible magic
        number from the binary file.

        Args:
            filespec (str): The file to get info for

        """
        # Some file names have varying magic numbers, but luckily then
        # naming convention is consistent for firmware.

        # print(f"FIXME: {filespec}")
        for pat, type_ in self.NAMETYPES:
            if pat.search(filespec):
                return type_

        # These are the top level blobs from the radio directory, and need to be
        # direct name match.
        name = os.path.basename(filespec)

        # breakpoint()
        if name in self.RADIOBLOBS:
            return self.RADIOBLOBS[name]

        log.debug(f"No type found for {filespec}, checking magic number")

        # breakpoint()
        # foo = magic.from_file(filespec)
        try:
            with open(filespec, "rb") as file:
                header = file.read(8)
                for ftype, num in self.MAGIC_NUMBERS:
                    if header.startswith(num):
                        log.debug(f"{filespec} is {ftype}")
                        # Handle GRAPHIC (png) manually or map to Bintypes.GRAPHIC
                        if ftype == "GRAPHIC":
                             return Bintypes.GRAPHIC
                        return Bintypes(ftype)
        except Exception:
            pass
        return Bintypes.UNKNOWN

    def find_files(self,
                   indir: str,
                   force_all: bool = False,
                   ) -> dict:
        """Find all the proprietary files for a device.

        Args:
            indir (str): The input directory with the extracted files
            force_all (bool): If True, ignore directory structure checks (for generic/ios)

        Return:
            (list): The files from the device
        """
        # spinner = Spinner('Scanning for files... ')
        for root, dirs, files in os.walk(indir):
            # spinner.next()
            base = Path(root)

            if not force_all:
                if root == indir:
                    continue
                if "META-INF" in base.parts:
                    continue
                # Ignore anything without vendor/build in the path.
                # base = Path(root.replace(f"{indir}/", ""))
                if len(base.parts) < 2:
                    continue

            # vendor = base.parts[0]
            # build = base.parts[1]
            # pat = re.compile("[a-z0-9*].[a-z][0-9][0-9]")
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
                    # Don't ignore in generic mode, maybe?
                    # For now keep ignoring known junk types to reduce noise.
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
