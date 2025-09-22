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

# base class to contain device data
import argparse
import logging
import os
from sys import argv
import sys
from pathlib import Path
import re
import json
import hashlib
from librephone.device_files import DeviceFiles

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

class DeviceData(DeviceFiles):
    def __init__(self,
                 vendor: str() = None,
                 model: str() = None,
                 build: str() = None,
                 ):
        """
        Returns:
            (Device): An instance of this class

        Args:
            vendor (str): The device vendor
            model (str): The device model
            build (str): The Android build tag

        Return:
            (Device): An instance of this class
        """
        self.vendor = vendor
        self.model = model
        self.build = build
        self.files = dict()
        self.soc = str()
        self.gpu = str()
        self.cpus = list()
        self.sensors = list()
        # self.keep = (".hex",".pb", ".img", ".bin", ".dat", ".fw", ".fw2")
        super().__init__()

    def file_data(self,
                  filename: str,
                  ):
        results = dict()
        if self.files["imgfiles"] is None:
            return results

        # FIXME: imgfiles shouldn't be hardcoded!
        for blob in self.files["imgfiles"]:
            if blob["file"] == filename:
                results["vendor"] = self.vendor
                results["model"] = self.model
                results["build"] = self.build
                results["size"] = blob["size"]
                results["file"] = filename

        return results

    def add_files(self,
                  column: str,
                  data: list,
                  ):
        self.files[column] = data

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

    dev = DeviceData("devices")
    if args.indir:
        files = dev.find_files(args.indir)

if __name__ == "__main__":
    """
    This is just a hook so this file can be run standlone during development.
    """
    main()
