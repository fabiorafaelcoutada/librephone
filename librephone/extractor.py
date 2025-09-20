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
from sys import argv
import logging
import os
import shutil
import sys
from pathlib import Path
import glob
from enum import IntEnum
import re
import psycopg
import zipfile
import glob
import subprocess
import shutil
from codetiming import Timer
# from tqdm import tqdm
# import tqdm.asyncio

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

# Based on https://wiki.lineageos.org/extracting_blobs_from_zips

# Before beginning, it is required to know the difference between the types of OTAs:

# Block-based OTA: the content of the system partition is stored inside of an
# .dat/.dat.br file as binary data. 

# File-based OTA: the content of the system partition is available inside a
# folder of the zip named system.

# Payload-based OTA: the content of the system partition is stored as an
# .img file inside of payload.bin.

# ota = f"{lineage}/prebuilts/extract-tools/linux-x86/bin/ota_extractor"
# sdat2img = f"{rootdir}/sdat2img.py"

class Extractor:
    def __init__(self,
                 yamlspec: str = f"partitions.yaml",
                 ):
        """
        Args:
            yamlfile (str): The config file to load

        Return:
            (Extractor): An instance of this class
        """
        self.sdat2img = f"{rootdir}/sdat2img/sdat2img.py"
        # Extract the build name from the zip file
        # package = glob.glob("*.zip")
        # if len(package) > 1:
        #     logging.error(f"No zip file found in directory!")
        #     quit()

        # tmp = package[0].split("-")
        self.build = None

        yaml = f"{rootdir}/{yamlspec}"
        if not os.path.exists(yaml):
            log.error(f"{yaml} does not exist!")
            quit()
            
        file = open(yaml, "r")
        self.yaml = load(file, Loader=Loader)
        file.close()

        self.devices = list()
        config = f"{rootdir}/devices.lst"
        if os.path.exists(config):
            with open(config, 'r') as file:
                for line in file.readlines():
                    tmp = line.split(':')
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
        zip = zipfile.ZipFile(package, 'w')
        meta = Path(".")
        print("Writing metadata to {package}")
        for file in meta.rglob("META-INF/com/android/*"):
            zip.write(file, arcname=file.relative_to(meta))

        for file in files:
            print(f"Writing {file} to {package}, which may take awhile...")
            zip.write(file)

    def decompress(self,
                   mdir: str = '.',
                   version: float = 22.2,
                   ) -> bool:
        """
        Extract files from a zip file.

        Args:
            mdir (str): The directory with the zip file
            version (float): The Lineage version to process

        Returns:
            (bool): Whether it worked or not
        """
        # Find the right zip file
        # breakpoint()
        if mdir.find(".zip") > 0:
            package = mdir
        else:
            package = glob.glob(f"{mdir}/*{version}*.zip")
        if len(package) == 0:
            logging.error(f"No lineage zip file in {mdir}!")
            return False
        else:
            package = package[0]

        # Extract the build name from the zip file
        tmp = package.split("-")
        self.build = tmp[4]

        # Extract all the files
        if not os.path.exists(f"{mdir}/payload.bin") and not os.path.exists(f"{mdir}/system.new.dat.br"):
            logging.info(f"Decompressing {package}")
            with zipfile.ZipFile(package, 'r') as zip:
                zip.extractall(mdir)
        else:
            logging.debug(f"{mdir} already decompressed.")
        return True

    def clone(self,
              lineage: str,
              indir: str = ".",
              outdir: str = "/tmp/",
              ) -> bool:
        """
        If the filesystem images are mounted, use the proprietary-*.txt
        files to clone all the blobs and proprietary files so they can be analyzed.

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
        tmp = abspath.parts

        timer.start()
        # The primary binary blobs are in the top level directory before
        # needing to mount anything.
        raddir = f"{outdir}/{tmp[len(tmp) - 2]}/{build}/radio"
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
        devdir = f"{tmp[len(tmp) - 2].lower()}/{build}"
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
                fd = open(deps, 'r')
                for depdir in eval(fd.read()):
                    subprops = f"{os.path.dirname(propdir)}/{os.path.basename(depdir["target_path"])}/{os.path.basename(devdir)}"
                    props = glob.glob(f"{subprops}/proprietary-*.txt")
                fd.close()

        keep = (".hex",".pb", ".img", ".bin", ".dat", ".fw", ".fw2")

        # Mount the extracted filesystems from the install packages
        self.unmount(indir)
        self.mount(indir)

        # If nothing was found, then the device directories hadn't been
        # downloaded from Lineage.
        if len(props) == 0:
            with open(f"{propdir}/proprietary-files.txt", 'w') as propout:
                mounted = str()
                for root, dirs, files in os.walk(indir):
                    if Path(root).is_mount():
                        mounted = os.path.basename(root)
                        # print(f"MOUNTED: {mounted}")
                    for file in files:
                        # if root == propdir:
                        #    continue
                        path = Path(file)
                        if path.suffix in keep:
                            dir = root.replace(f"{indir}", "")
                            if len(dir) == 0:
                                continue
                            # FIXME: there has got to be a better way to do this.
                            if root.find(outdir) > 0 or root.find("META-INF") > 0:
                                continue
                            # print(f"FIXME: {root} {dir}/{file}")
                            # print(f"{mounted}/{file}\n")
                            # print(f"{root.replace("./", "")}/{file}\n")
                            propout.write(f"{dir}/{file}\n")
            logging.info(f"Wrote {propdir}/proprietary-files.txt")
            props = [f"{propdir}/proprietary-files.txt"]

        # Process the lists of proprietary files
        for file in props:
            data = self.parse_proprietary_file(f"{file}")
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
                    logging.debug(f"Copying {indir}/{src} to {dst}")
                    if not os.path.exists(dst):
                        shutil.copy(f"{indir}/{src}", dst, follow_symlinks=False)
        timer.stop()
        self.unmount(indir)

    def extract(self,
                mdir: str,
                ) -> bool:
        """
        Extract files from an install package. If there is a
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
            self.decompress(mdir, 22.2)

        if os.path.exists(f"{mdir}/payload.bin"):
            # for file in glob.glob(f"{mdir}/*.img"):
            #     os.remove(file)
            if len(glob.glob(f"{mdir}/*.img")) == 0:
                logging.info(f"Extracting files from {mdir}/payload.bin")
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
            logging.error(f"There are no transfer lists in {mdir}!")
            return False

        for transfer in files:
            dat = transfer.replace(f".transfer.list", ".new.dat.br")
            img = transfer.replace(f".transfer.list", ".img")
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
        """
        Mount all filesystem images.

        Arg:
            mdir (str): The directory containing the image files

        Returns:
            (bool): The result of mounting the filesystems
        """
        logging.info("Mounting all filesystems")
        if not os.path.exists(f"{mdir}/system.img"):
            logging.error(f"{mdir}/system.img doesn't exist!")
            return False

        # if not os.path.exists(f"{mdir}/system"):
        #     os.mkdir(f"{mdir}/system")

        # if not os.path.ismount(f"{mdir}/system"):
        #     # This is always mounted for all devices
        #     result = subprocess.run(
        #     [
        #         "sudo",
        #         "mount",
        #         f"{mdir}/system.img",
        #         f"{mdir}/system",
        #     ]
        #     )
        #     if result.returncode != 0:
        #         logging.error(f"Failed to mount system image!")
        #         return False

        # Some devices mount product and vendor under system, but
        # others expect it to be mounted top level.
        fs = {"system.img": "system/",
              "odm.img": "system/odm/",
              "product.img": "system/product/",
              "product.img": "product/",
              "vendor.img": "system/vendor/",
              "vendor.img": "vendor/",
              "system_ext.img": "system/system_ext/"
              }

        for dev, img in fs.items():
            if os.path.exists(f"{mdir}/{dev}"):
                if not os.path.exists(f"{mdir}/{img}"):
                    os.mkdir(f"{mdir}/{img}")
                if not os.path.ismount(f"{mdir}/{img}"):
                    logging.info(f"Mounting image {dev} to {mdir}/{img}")
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
        """
        Unmount all the mounted filesystems.

        Arg:
            mdir (str): The directory containing the image files
        """
        logging.info(f"Unmounting all filesystems in {mdir}")
        dirs = ("system", "vendor", "product")
        for mounted in dirs:
            if not os.path.ismount(f"{mdir}/{mounted}"):
                logging.debug("\tNothing mounted")
                return True
            if os.path.exists(f"{mdir}/{mounted}"):
                result = subprocess.run(
                    [
                        "sudo",
                        "umount",
                        "-R",
                        f"{mdir}/{mounted}",
                    ]
                )
        # Remove created directories
        shutil.rmtree(f"{mdir}/system")

    def parse_proprietary_file(self,
                               filespec: str = None,
                               ) -> dict:
        """
        Parse the proprietaryu-*.txt files Lineage uses as the list of files needed.

        Args:
            filespec (str): The proprietary files data file

        Return:
            (dict) The data from the file
        """
        if filespec is None:
            logging.error(f"You need to specify a file to parse!")
            return

        # print(propfile)
        ignore = [".xml", ".rc", ".cfg", ".txt"]
        logging.info(f"Parsing {filespec}...")
        files = dict()
        with open(filespec, 'r') as file:
            for line in file:
                if line[:1] == "#" or line == '\n':
                    continue
                line = line.rstrip()
                # Some entries have a trailing column
                root = line.split('/')[0]
                # which goes in the output director/y
                colon = line.find(':')
                signed = line.find(';')
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
        """
        Delete all generated files leavihng only the zip file.

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
                    shutil.rmtree(f"{mdir}/{file}")
                else:
                    os.remove(f"{mdir}/{file}")

        if os.path.exists(f"{mdir}/META-INF"):
            shutil.rmtree(f"{mdir}/META-INF")
        if os.path.exists(f"{mdir}/install"):
            shutil.rmtree(f"{mdir}/install")

    def dump(self):
        """
        Dump the contents of the YAML file to the terminal for debugging.
        """
        print(dump(self.yaml, Dumper=Dumper))
        
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
    # parser.add_argument("-b", "--build",
    #                     help="Specify the build name")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Do all operations")
    parser.add_argument("-o", "--outdir", default="blobs", help="The output directory")
    parser.add_argument("-c", "--clone",
                        help="Copy the proprietary files for analysis")
    # parser.add_argument("-p", "--package",
    #                     help="Make the the zip package")
    args = parser.parse_args()

    # Need at least one operation
    if len(argv) == 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    # Top level Lineage source tree
    lineage = "/work/Lineage-22.2"
    base = os.getenv("LINEAGE")
    if base:
        lineage = base

    extract = Extractor()
    # extract.dump()

    doall = False
    if args.all:
        doall = True

    version = 22.2
    # Decompress the zip file
    if args.unzip or doall:
        extract.decompress(args.unzip, version)

    # Extract files
    if args.extract or doall:
        # extract.decompress(args.unzip)
        extract.extract(args.extract)

    # Mount the files
    if args.mount or doall:
        logging.error(f"Need to specify the directory with the files")
        extract.mount(args.mount)
        
    if args.clone:
        # path = Path(args.clone)
        extract.clone(lineage, args.clone, args.outdir)
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
