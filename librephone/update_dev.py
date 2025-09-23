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
from sys import argv
from pathlib import Path
import glob
import hashlib
import magic
from enum import IntEnum
import re
import psycopg
import json
from librephone.device import DeviceData
import csv

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class UpdateDevice(object):
    def __init__(self):
        """
        Returns:
            (QueryDevice): An instance of this class
        """
        # FIXME: this needs to be configurable
        self.dbname = "devices"
        connect = f"dbname='{self.dbname}'"
        self.dbshell = psycopg.connect(connect, autocommit=True)
        # self.dbshell = psycopg2.connect(connect)
        self.dbcursor = self.dbshell.cursor()
        if self.dbcursor.closed != 0:
            logging.error(f"Couldn't open database!")
        self.devices = list()
        self.lineage = os.getenv("LINEAGE")

    def set_column(self,
            column: str = None,
            build: str = None,
            value: str = None,
            ) -> bool:
        """
        Set a column for a device.

        Args:
        """
        if column is None or build is None or value is None:
            logging.error(f"Need to specify all the parameters!")
            return False

        sql = f"UPDATE devices SET {column} = '{value}' WHERE build='{build}'"
        print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)        

    def set_columns(self,
                    values: dict,
                    ) -> bool:
        """
        Set multiple columns for a device.

        Args:
        """
        sql = f"UPDATE devices SET "
        build = values["build"]
        del values["build"]
        for key, value in values.items():
            if len(value) == 0:
                continue
            sql += f" {key} = '{value}',"
        sql = sql[:-1]
        sql += f" WHERE build='{build}'"
        if sql.find("SET WHERE") > 0:
            return
        # print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)
        
def main():
    """This main function lets this class be run standalone by a bash script."""
    choices = ("soc", "released", "builds")
    parser = argparse.ArgumentParser(description="Query device data in postgres")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-s", "--set", choices=choices, help="Set device metadata")
    parser.add_argument("-c", "--csv", help="Import from CSV file")
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
        
    devdb = UpdateDevice()

    if args.csv:
        # This reads in the data/builds.csv file, which keeps track of
        # build status
        with open(f"{rootdir}/{args.csv}", newline="", encoding="latin") as file:
            reader = csv.DictReader(file, delimiter=",")
            for row in reader:
                entry = {"build": row["Build"],
                         "soc": row["SOC"],
                         "released": row["Released"],
                         }
                if row["Build 22.2"] == "completes":
                    entry["builds"] = 't'
                if row["Extract 22.2"] == "completes":
                    entry["extracts"] = 't'
                devdb.set_columns(entry)
    elif args.set:
        devdb.set_column("builds", build, True)
        devdb.set_column("released", build, True)
        devdb.set_column("soc", build, )
    # devdb.dump()

if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
