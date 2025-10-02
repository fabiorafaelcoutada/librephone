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
import logging
import os
import shutil
import sys
from pathlib import Path
import glob
import hashlib
import magic
from enum import IntEnum
import re
import psycopg
from sys import argv
import json
from librephone.device import DeviceData
from librephone.typedefs import Cputypes, Gpumodels, Devstatus, Imgtypes, Bintypes, Archtypes, Celltypes, Nettypes, Wifitypes, Filetypes, Blobtypes
from librephone.update_dev import UpdateDevice

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class DeviceImport(UpdateDevice):
    def __init__(self,
                 dbname: str = "devices",
                 ):
        """
        Args:
            dbname (str): The database name for device data
        
        Return:
            (DeviceImport): An instance of this class
        """
        # These are populated after scanning the files
        self.proprietary = list()
        self.blobs = list()
        self.files = dict()
        self.firmware = list()

        connect = f"dbname='{dbname}'"
        self.dbshell = psycopg.connect(connect, autocommit=True)
        self.dbcursor = self.dbshell.cursor()
        if self.dbcursor.closed != 0:
            log.error(f"Couldn't open database!")
        else:
            log.info(f"Connected to {dbname}")

        self.links = dict()
        # self.keep = (".hex", ".pb", ".img", ".bin", ".dat", ".fw", ".fw2")
        self.keep = (".hex", ".img", ".bin", ".dat", ".fw", ".fw2")

    def create_entry(self,
                     vendor: str,
                     model: str,
                     build: str,
                     ):
        sql = f"INSERT into devices(vendor, model, build) VALUES('{vendor}', '{model}', '{build}') ON CONFLICT (build) DO UPDATE SET vendor='{vendor}', model='{model}' WHERE devices.build='{build}'"
        log.info(f"Bootstrapping {vendor}, {model}, {build}: {sql}")
        print(sql)
        result = self.dbcursor.execute(sql)

    def bootstrap(self,
                  filespec: str,
                  ):
        """
        This bootstraps the database with statc data.
        """
        # This is the CSV file produced by image_utils -l that sets
        # the vendor, model, and build columns need by all the other
        # database queries
        datafile = open(filespec, "r")
        for line in datafile.readlines():
            parts = line.rstrip().split(':')
            self.create_entry(parts[0], parts[2], parts[1])
        datafile.close()

        # This is the spreadsheet of build status that sets several columns
        # like soc and released.
        self.process_file(f"{os.path.dirname(rootdir)}/data/builds.csv")

    def write_db(self,
                 device: DeviceData
                 ) -> bool:
        """
        Write the metadata for a device build to the database.

        Args:
            device (DeviceData): The metadata for this file

        Returns:
            (bool): If writing the data suceeded
        """
        # queries = dict()
        # for suffix, files in files.items():
        #     if suffix not in queries:
        #         queries[suffix] = list()
        #     item = json.dumps(files)
        #     queries[suffix].append(item)
        #     # print(f"SQL: {item}")


        sql = str()
        # sort by type
        for category, files in device.files.items():
            log.info(f"Processing the {category} file type, has {len(files)} files")
            # if category in Imgtypes :
            #     column = "imgfiles"
            # elif category in Bintypes:
            #     column = "binfiles"
            # # elif category == "FIRMWARE":
            # #     column = "firmware"
            # elif category == "HEX":
            #     column = "hexfiles"
            # else:
            #     suffix = Path(files[0]["file"]).suffix
            #     log.debug(f"Unsupported type: {category} for file suffix {suffix}")
            #     continue

            sql = f"SELECT jsonb_array_length(blobs) FROM devices WHERE build='{device.build}'"
            # print(f"SQL: {sql}")
            result = self.dbcursor.execute(sql)
            # None as a result means no entries in the jsonb column
            count = result.fetchone()
        
            # print(result.fetchone())
            # You can't update a jsonb column that is empty, so the first entry
            # is basically an insert.
            if count is not None and count[0] is not None:
                sql = f"UPDATE devices SET blobs = blobs || '{json.dumps(files)}' WHERE build='{device.build}'"
            else:
                sql = f"UPDATE devices SET blobs = '{json.dumps(files)}' WHERE build='{device.build}'"
            # print(f"SQL: {sql}")
            result = self.dbcursor.execute(sql)

    def dump(self):
        print(f"Dumping a Device from {os.path.abspath(self.directory)}")
        for dev in self.files:
            dev.dump()

def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Import device data into postgres")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--indir", help="The top level vendor directory")
    # parser.add_argument("-o", "--outdir", default="blobs", help="The output directory")
    parser.add_argument("-f", "--file", help="Get data for a file, only for debugging")
    parser.add_argument("-b", "--bootstrap", action="store_true",
                        help="Bootstrap a table with minimal data")
    # parser.add_argument("-c", "--company", help="The vendor name")
    #parser.add_argument("-m", "--model", help="The model name")
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

    # The top level directory to scan for proprietary files
    # toplevel = os.curdir
    if args.indir is not None:
        toplevel = args.indir

    # Extract the probable vendor and device model from the path.

    links = dict()

    devimport = DeviceImport("devices")
    if args.bootstrap:
        # with open(f"{rootdir}/devices.lst", 'r') as file:
        #     for line in file:
        #         tmp = line.split(':')
        #         links[tmp[0]] = tmp[1].rstrip()
        devimport.bootstrap(f"{rootdir}/devices.lst")
        quit()

    if args.file:
        metadata = dev.get_metadata(args.file)
        print(metadata)
    elif args.indir:
        # Always use an absolute path. Path.resolve() returns the actual
        # directory, whereass os.path returns the path with the symbolic link
        # name. We want both.
        indir = os.path.abspath(args.indir)
        build = os.path.basename(indir)
        model = os.path.basename(Path(args.indir).resolve())
        vendor = os.path.basename(os.path.dirname(indir))
        # dev = DeviceData(vendor=vendor, model=model, build=build)
        dev = DeviceData(vendor=vendor, build=build)        
        files = dev.find_files(args.indir)
        devimport.write_db(dev)

if __name__ == "__main__":
    """
    This is just a hook so this file can be run standlone during development.
    """
    main()
