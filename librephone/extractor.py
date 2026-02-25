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

import argparse
import ast
import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from sys import argv

from codetiming import Timer

# from tqdm import tqdm
# import tqdm.asyncio
# from ext4 import Volume
# import unblob
import librephone as pt
from librephone.device_files import DeviceFiles

rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

# Based on https://wiki.lineageos.org/extracting_blobs_from_zips

class Extractor:
    def __init__(self,
                 ):
        """Args:
            yamlfile (str): The config file to load

        Return:
            (Extractor): An instance of this class
        """
        self.build = None
        self.devices = list()
        config = f"{rootdir}/devices.lst"
        if os.path.exists(config):
            with open(config, "r") as file:
                for line in file.readlines():
                    tmp = line.split(":")
                    self.devices.append({"vendor": tmp[0],
                                         "build": tmp[1],
                                         "model": tmp[2].rstrip()}
                                        )

    def get_devpath(self,
                    ident: str,
                    ):
        """
        """
        for dev in self.devices:
            if dev["build"] == ident:
                return dev["model"]
            elif dev["model"] == ident:
                return dev["build"]
        return "unknown"

    def package(self,
                package: str = "lineage.zip",
                ):
        files = ("apex_info.pb",
                  "care_map.pb",
                  "payload.bin",
                  "payload_properties.txt",
                  )
        # Extract all the files
        logging.info(f"Creating install package: {package}")
        zip = zipfile.ZipFile(package, "w")
        meta = Path(".")
        print("Writing metadata to {package}")
        for file in meta.rglob("META-INF/com/android/*"):
            zip.write(file, arcname=file.relative_to(meta))

        for file in files:
            print(f"Writing {file} to {package}, which may take awhile...")
            zip.write(file)

    def decompress(self,
                   mdir: str = ".",
                   version: float = 23.0,
                   ) -> bool:
        """Extract files from a zip file.

        Args:
            mdir (str): The directory with the zip file
            version (float): The Lineage version to process

        Returns:
            (bool): Whether it worked or not
        """
        # Find the right zip file
        if mdir.find(".zip") > 0:
            package = mdir
        else:
            package = glob.glob(f"{mdir}/*{version}*.zip")
        if len(package) == 0:
            logging.warning(f"No lineage zip file in {mdir} for 23.0!")
            return False
        else:
            package = package[0]

        # Extract the build name from the zip file
        tmp = package.split("-")
        try:
            self.build = tmp[4]
        except IndexError:
            self.build = "unknown"

        # Extract all the files

        # FIXME: some of the Lineage packages have a potential zip bomb error
        # when using the zip module, which the command line unzip doesn't
        # have, so use that for now.
        os.environ["UNZIP_DISABLE_ZIPBOMB_DETECTION"] = "TRUE"
        if not os.path.exists(f"{mdir}/payload.bin") and not os.path.exists(f"{mdir}/system.new.dat.br"):
            logging.info(f"Decompressing {package}")
            # result = subprocess.run(
            #     [
            #         "/usr/bin/unzip ",
            #         "${package}",
            #         "-d",
            #         mdir,
            #         ]
            # )
            with zipfile.ZipFile(package, "r") as zip:
                zip.extractall(mdir)
        else:
            logging.debug(f"{mdir} already decompressed.")
        return True

    def clone_generic(self,
                      indir: str,
                      outdir: str,
                      ) -> bool:
        """Clone all interesting files from a generic Android or iOS dump.
        This is used when no proprietary-files.txt is available.
        """
        logging.info("Starting generic extraction/cloning...")
        dev = DeviceFiles()
        # Use force_all=True to ignore directory structure constraints
        files = dev.find_files(indir, force_all=True)

        count = 0
        for ftype, file_list in files.items():
            for file_data in file_list:
                src_path = os.path.join(file_data["path"], file_data["file"])
                # Calculate relative path to preserve structure
                try:
                    rel_path = os.path.relpath(src_path, indir)
                except ValueError:
                    # If src_path is not relative to indir (e.g. symlink resolution), just use basename?
                    # Or skip?
                    rel_path = file_data["file"]

                dst_path = os.path.join(outdir, rel_path)

                if not os.path.exists(os.path.dirname(dst_path)):
                    os.makedirs(os.path.dirname(dst_path))

                if not os.path.exists(dst_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        count += 1
                    except Exception as e:
                        logging.warning(f"Failed to copy {src_path}: {e}")

        logging.info(f"Generic cloning complete. Copied {count} files.")
        return True

    def clone(self,
              lineage: str,
              indir: str = ".",
              outdir: str = "/tmp/",
              ios_mode: bool = False,
              ) -> bool:
        """If the filesystem images are mounted, use the proprietary-*.txt
        files to clone all the blobs and proprietary files so they can be analyzed.
        If ios_mode is True or proprietary-files.txt is missing, perform generic extraction.

        Args:
            indir (str): The top level directory to scan for files
            outdir (str): The output directory for all files

        Return:
            (bool): If the cloning was sucessful
        """
        timer = Timer(text="clone() took {seconds:.0f}s")
        if not indir:
            if not os.path.exists(indir):
                logging.error(f"{indir} does not exist!")
                return False
        if not os.path.exists(outdir):
            logging.debug(f"Making output directory {outdir}")
            os.mkdir(outdir)

        abspath = Path(indir).resolve()
        build = self.get_devpath(os.path.basename(abspath))

        # Handle cases where path parsing fails
        tmp = abspath.parts
        if len(tmp) >= 2:
            # Try to guess structure
            pass

        timer.start()

        if ios_mode:
             # Skip Android specific mounting/radio copy if strictly iOS mode
             # But if it's a directory dump, we just clone.
             return self.clone_generic(indir, outdir)

        # The primary binary blobs are in the top level directory before
        # needing to mount anything.
        # raddir = f"{outdir}/{tmp[len(tmp) - 2]}/{build}/radio"
        # Robust path construction
        try:
             raddir = f"{outdir}/{tmp[-2]}/{build}/radio"
        except IndexError:
             raddir = f"{outdir}/unknown/{build}/radio"

        if not os.path.exists(raddir):
            os.makedirs(raddir)
        ignore = re.compile("(system|vendor|product|odm).*")
        for img in glob.glob(f"{abspath}/*.img"):
            if re.search(ignore, img):
                logging.debug(f"Ignoring package {img}")
                continue
            if os.path.exists(img):
                logging.debug(f"Copying {img} to {raddir}")
            shutil.copy(img, raddir)

        # build = self.get_devpath(tmp[len(tmp) - 1])
        try:
            devdir = f"{tmp[-2].lower()}/{build}"
        except IndexError:
            devdir = f"unknown/{build}"

        propdir = f"{lineage}/device/{devdir}"

        propfile = f"{propdir}/proprietary-files.txt"
        props = list()
        if os.path.exists(propfile):
            props = glob.glob(f"{propdir}/proprietary-*.txt")
        elif os.path.exists(f"{propdir}/{build}/proprietary-files.txt"):
            props = glob.glob(f"{propdir}/{build}/proprietary-*.txt")

        if len(props) == 0:
            deps = f"{propdir}/lineage.dependencies"
            if os.path.exists(deps):
                fd = open(deps, "r")
                try:
                    # SENTINEL: Use ast.literal_eval() instead of eval() to prevent arbitrary code execution
                    # while maintaining support for Python literals (like single quotes).
                    for depdir in ast.literal_eval(fd.read()):
                        target_base = os.path.basename(depdir['target_path'])
                        dev_base = os.path.basename(devdir)
                        subprops = f"{os.path.dirname(propdir)}/{target_base}/{dev_base}"
                        props = glob.glob(f"{subprops}/proprietary-*.txt")
                except Exception:
                    pass
                fd.close()

        # Mount the extracted filesystems from the install packages
        self.unmount(indir)
        self.mount(indir)

        if len(props) == 0:
            # Fallback to generic extraction
            logging.info("No proprietary-files.txt found. Falling back to generic extraction.")
            self.clone_generic(indir, outdir)
            self.unmount(indir)
            timer.stop()
            return True

        keep = (".hex",
                ".pb",
                ".img",
                ".bin",
                ".dat",
                ".mdt",
                ".fw",
                ".fw2")

        # Process the lists of proprietary files
        for file in props:
            data = self.parse_proprietary_file(file)
            for dir, files in data.items():
                for entry in files:
                    # breakpoint()
                    src = entry["src"]
                    # Ignore any file that starts with a hypen
                    if src[:1] == "-":
                        # logging.debug(f"Ignoring {src}")
                        continue
                    dst = entry["dst"]
                    if dst is None:
                        sub = src.replace(lineage, "")
                        dst = f"{outdir}/{devdir}/{sub}"
                    else:
                        dst = f"{devdir}/{dst.rstrip()}"
                    if Path(src).suffix not in keep:
                        continue
                    if not os.path.exists(os.path.dirname(dst)):
                        logging.debug(f"Creating output directory {os.path.dirname(dst)}")
                        os.makedirs(os.path.dirname(dst))
                        # shutil.copy(src, dst)
                    if not os.path.exists(f"{indir}/{src}"):
                        log.error(f"File {indir}/{src} does not exist, but it should!")
                        continue
                    if not os.path.exists(dst):
                        logging.debug(f"Copying {indir}/{src} to {dst}")
                        shutil.copy(f"{indir}/{src}", dst, follow_symlinks=False)
        files = ["modem", "bluetooth"]
        for blob in files:
            for root, dirs, files in os.walk(f"{indir}/{blob}/image"):
                if len(files) == 0:
                    continue
                for src in files:
                    if Path(src).is_symlink():
                        logging.debug(f"{src} is a symbolic link")
                        continue
                    # breakpoint()
                    dst = f"{outdir}/{devdir}/{blob}/image/"
                    if not os.path.exists(dst):
                        os.makedirs(dst)
                    path = Path(root)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    # if not os.path.exists(dst):
                    logging.debug(f"Copying {path}/{src} to {dst}")
                    shutil.copy(f"{path}/{src}", dst, follow_symlinks=False)
        timer.stop()
        self.unmount(indir)

    def extract(self,
                mdir: str,
                ) -> bool:
        """Extract files from an install package. If there is a
        .dat or .dat.br it's block based OTA. If there is a payload.bin
        file, it's payload based OTA.

        Arg:
            mdir (str): The directory containing the image files

        Returns:
            (bool): The result of the subprocess
        """
        timer = Timer(text="extract() took {seconds:.0f}s")
        timer.start()
        if not os.path.exists(f"{mdir}/payload.bin"):
            # FIXME: don't hardcode the version
            self.decompress(mdir, 23.0)

        if os.path.exists(f"{mdir}/payload.bin"):
            # for file in glob.glob(f"{mdir}/*.img"):
            #     os.remove(file)
            if not os.path.exists(f"{mdir}/vendor.img"):
                logging.info(f"Extracting files from {mdir}/payload.bin")
                # self.clean(mdir)
                result = subprocess.run(
                    [
                        "otadump",
                        "--concurrency",
                        "8",
                        "--output-dir",
                        mdir,
                        f"{mdir}/payload.bin",
                    ]
                )
                # logging.debug(f"RUN: {result.args}")
            else:
                logging.info(f"Files already extracted in {mdir}")
            return True

        for file in glob.glob(f"{mdir}/*.br"):
            new = file.replace(".br", "")
            logging.info(f"Uncompressing brotli file {file}")
            result = subprocess.run(
                [
                    "brotli",
                    "--decompress",
                    f"--output={new}",
                    file,
                ]
            )
            # logging.debug(f"RUN: {result.args}")

        # Convert sparse Android sparse image (.dat) into filesystem
        # ext4 image (.img)
        files = glob.glob(f"{mdir}/*.transfer.list")
        if len(files) == 0:
            # If no transfer list, check if we have .img files directly or if generic mode
            logging.warning(f"There are no transfer lists in {mdir}! Assuming extracted images or Generic/iOS mode.")
            return False

        for transfer in files:
            dat = transfer.replace(".transfer.list", ".new.dat.br")
            img = transfer.replace(".transfer.list", ".img")
            logging.info(f"Converting {file} to ext4 image")
            result = subprocess.run(
                [
                    "sdat2img-brotli",
                    "-d",
                    dat,
                    "-t",
                    transfer,
                    "-o",
                    img,
                ]
            )
            # logging.debug(f"RUN: {result.args}")
        timer.stop()

    def mount(self,
              mdir: str,
              ):
        """Mount all filesystem images.

        Arg:
            mdir (str): The directory containing the image files

        Returns:
            (bool): The result of mounting the filesystems
        """
        logging.info("Mounting all filesystems")
        if not os.path.exists(f"{mdir}/system.img"):
            # In generic mode or iOS mode, system.img might not exist
            logging.warning(f"{mdir}/system.img doesn't exist! Skipping mount.")
            return False

        # Some devices mount product and vendor under system, but
        # others expect it to be mounted top level. We mount in
        # multiple places to cover all the variations in the
        # proprietary-diles.txt files.
        fs = {"system.img": "system/",
              "odm.img": "system/odm/",
              "odm.img": "odm/",
              "product.img": "system/product/",
              "product.img": "product/",
              "vendor.img": "system/vendor/",
              "vendor.img": "vendor/",
              "system_ext.img": "system/system_ext/",
              "modem.img": "modem",
              "bluetooth.img": "bluetooth",
              }

        for dev, img in fs.items():
            if os.path.exists(f"{mdir}/{dev}"):
                if not os.path.exists(f"{mdir}/{img}"):
                    os.mkdir(f"{mdir}/{img}")
                if not os.path.ismount(f"{mdir}/{img}"):
                    logging.info(f"Mounting image {dev} to {mdir}/{img}")
                    # debugfs -R rdump / f"{mdir}/{img}" f"{mdir}/{dev}"
                    result = subprocess.run(
                    [
                        "sudo",
                        "mount",
                        "-m",
                        "-w",
                        f"{mdir}/{dev}",
                        f"{mdir}/{img}",
                    ]
                    )
                else:
                    logging.info(f"Image {mdir}/{img} is already mounted")

        return True

    def unmount(self,
                mdir: str,
                ):
        """Unmount all the mounted filesystems.

        Arg:
            mdir (str): The directory containing the image files
        """
        logging.info(f"Unmounting all filesystems in {mdir}")
        dirs = ("system", "vendor", "product", "modem", "odm", "system_ext", "bluetooth")
        # breakpoint()
        for mounted in dirs:
            if os.path.exists(f"{mdir}/{mounted}"):
                if not os.path.ismount(f"{mdir}/{mounted}"):
                    logging.debug(f"\t{mounted} isn't mounted")
                    continue
                logging.debug(f"Unmounting {mdir}/{mounted}")
                result = subprocess.run(
                [
                    "sudo",
                    "umount",
                    "-R",
                    f"{mdir}/{mounted}",
                ]
            )
        # Remove created directories
        # shutil.rmtree(f"{mdir}/system")

    def parse_proprietary_file(self,
                               filespec: str = None,
                               ) -> dict:
        """Parse the proprietaryu-*.txt files Lineage uses as the list of files needed.

        Args:
            filespec (str): The proprietary files data file

        Return:
            (dict) The data from the file
        """
        if filespec is None:
            logging.error("You need to specify a file to parse!")
            return

        # print(propfile)
        ignore = [".xml", ".rc", ".cfg", ".txt"]
        logging.info(f"Parsing {filespec}...")
        files = dict()
        with open(filespec, "r") as file:
            for line in file:
                if line[:1] == "#" or line == "\n":
                    continue
                line = line.rstrip()
                # Some entries have a trailing column
                root = line.split("/")[0]
                # which goes in the output director/y
                colon = line.find(":")
                signed = line.find(";")
                if signed == 0:
                    signed = len(line + 1)
                if colon < 0 and signed < 0:
                    src = line
                    dst = None
                elif colon < 0 and signed > 0:
                    src = line[:signed]
                    dst = line[signed + 1:]
                elif colon > 0 and signed < 0:
                    src = line[:colon]
                    dst = line[colon + 1:]
                elif colon > 0 and signed > 0:
                    src = line[:colon]
                    dst = line[colon + 1:]
                    sign = line[signed + 1:]
                if root not in files:
                    files[root] = list()
                try:
                    new = {"src": src, "dst": dst}
                except:
                    breakpoint()
                files[root].append(new)
                # print(new)

        return files

    def clean(self,
              mdir: str,
              ):
        """Delete all generated files leavihng only the zip file.

        Arg:
            mdir (str): The directory containing the image files
        """
        logging.info(f"Removing all generated files in {mdir}")
        self.unmount(mdir)
        if os.path.exists(f"{mdir}/system"):
            shutil.rmtree(f"{mdir}/system")

        for file in os.listdir(mdir):
            if "zip" not in file:
                if os.path.isdir(f"{mdir}/{file}"):
                    if os.path.islink(f"{mdir}/{file}"):
                        os.remove(f"{mdir}/{file}")
                    else:
                        shutil.rmtree(f"{mdir}/{file}")
                else:
                    os.remove(f"{mdir}/{file}")

        if os.path.exists(f"{mdir}/META-INF"):
            shutil.rmtree(f"{mdir}/META-INF")
        if os.path.exists(f"{mdir}/install"):
            shutil.rmtree(f"{mdir}/install")

    def dump(self):
        """Dump the contents of the YAML file to the terminal for debugging.
        """
        # print(dump(self.yaml, Dumper=Dumper))

def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Import device data into postgres")
    epilog="""
This script requires the Lineage install package is already downloaded.
Execute this script in the directory with the zip file which will then
unpack all the files, and mount the filesystems so the files can accessed.
    
    """
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="verbose output")
    parser.add_argument("-i", "--indir",
                        help="The top level device directory")
    parser.add_argument("-z", "--unzip",
                        help="Decompress the zip file")
    parser.add_argument("-e", "--extract",
                        help="Extract all unzipped files")
    parser.add_argument("-m", "--mount",
                        help="Mount all filesystems"),
    parser.add_argument("-u", "--unmount",
                        help="Unmount all filesystems")
    parser.add_argument("-r", "--remove",
                        help="Clean all generated file")
    parser.add_argument("-l", "--lineage", default=23.0,
                        help="Specify the Lineage version")
    # parser.add_argument("-b", "--build",
    #                     help="Specify the build name")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Do all operations")
    parser.add_argument("-o", "--outdir", default="blobs", help="The output directory")
    parser.add_argument("-c", "--clone",
                        help="Copy the proprietary files for analysis")
    parser.add_argument("--ios", action="store_true",
                        help="Enable iOS extraction mode")
    parser.add_argument("--generic", action="store_true",
                        help="Enable Generic Android extraction mode")
    # parser.add_argument("-p", "--package",
    #                     help="Make the the zip package")
    args = parser.parse_args()

    # Need at least one operation
    if len(argv) == 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Top level Lineage source tree
    lineage = "/work/Lineage-23.0"
    base = os.getenv("LINEAGE")
    if base:
        lineage = base

    extract = Extractor()
    # extract.dump()

    doall = False
    if args.all:
        doall = True

    # Decompress the zip file
    if args.unzip or doall:
        extract.decompress(args.unzip, args.lineage)

    # Extract files
    if args.extract or doall:
        # extract.decompress(args.unzip)
        extract.extract(args.extract)

    # Mount the files
    if args.mount or doall:
        extract.mount(args.mount)

    if args.clone:
        # path = Path(args.clone)
        # Determine mode
        ios_mode = args.ios
        if args.generic:
            # Generic flag forces generic logic which handles both in clone_generic
            pass

        extract.clone(lineage, args.clone, args.outdir, ios_mode=ios_mode)
        logging.info(f"All done cloning {args.clone} into {args.outdir}")
        quit()

    # Unmount the files
    if args.unmount:
        if args.unmount:
            extract.unmount(args.unmount)
        else:
            extract.unmount(args.mount)

    if args.remove:
        extract.unmount(args.remove)
        extract.clean(args.remove)

    # if args.package:
    #     extract.package(args.package)

if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
