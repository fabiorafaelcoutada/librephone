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
from librephone.typedefs import Bintypes
from progress.bar import Bar

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class QueryDevice(object):
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
        # self.columns = ("imgfiles", "binfiles", "firmware", "hexfiles")
        self.keep = (".hex", ".img", ".bin", ".dat", ".fw", ".fw2")

    def get_metadata(self):
        """
        Query a table in the database.

        Args:
            field (str): The filed to get data for
        Returns:
            (list): The results of the query
        """
        sql = f"SELECT vendor, model, build FROM {self.dbname}"
        # print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)
        result = self.dbcursor.fetchone()
        # print(result)
        return result

    def list_count(self) -> dict:
        """
        Query a table in the database.

        Args:

        Returns:
            (list): The results of the query
        """
        sql = f"SELECT vendor,model,build,jsonb_array_length(blobs) FROM {self.dbname} ORDER BY jsonb_array_elements(blobs)"
        # print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()
        # print(result)
        return result

    def list_totals(self,
                    bintype: Bintypes,
                    ) -> list:
        """
        Query a table in the database.

        Returns:
            (list): The results of the query
        """
        breakpoint()
        sql = f"SELECT vendor,model,build FROM {self.dbname},jsonb_array_elements(blobs->'type') foo WHERE blobs  @> '[{{\"type\": \"{bintype.value}\"}}]';"
        # print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()
        # print(result)
        return result

    def list_elements(self,
                       op: str = "len",
                       ) -> list:
        """
        Query a table in the database.

        Args:

        Returns:
            (list): The results of the query
        """
        if op == "len":
            sql = f"SELECT vendor,model,build,blobs FROM {self.dbname} ORDER BY jsonb_array_length(jsonb_array_elements(blobs))"
            # print(f"SQL: {sql}")
            result = self.dbcursor.execute(sql)
            result = self.dbcursor.fetchall()
            # print(result)
            return result

    def dump(self):
        for dev in self.devices:
            dev.dump()

    def track_file(self,
                   filename: str,
                   ) -> list:
        """
        Query a table in the database.

        Args:
            column (str): The column to get data from
            filename (str): The filename to track
        Returns:
            (list): The devices the file is in
        """
        file = str({"file": filename}).replace("'", '"')
        sql = f"SELECT ARRAY_AGG(model) FROM devices WHERE blobs @> '[{file}]';"
        # print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()

        return result

    def track_size(self,
                   ) -> list:
        """
        Query a table in the database.

        Args:

        Returns:
            (list): The devices the file is in
        """
        sql = f"SELECT vendor,model,build,foo->>'file',foo->>'size',foo->>'md5sum',foo->>'type' FROM devices,jsonb_array_elements(devices.blobs) AS foo;"
        # print(f"SQL: {sql}")
        result = self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()

        return result

    def list_devices(self,
                     ) -> list:
        """
        List all the devices containing a file.

        """
        devices = list()
        sql = f"SELECT DISTINCT(foo->>'file') FROM devices,jsonb_array_elements(devices.blobs) AS foo;"
        result = self.dbcursor.execute(sql)
        files = self.dbcursor.fetchall()

        bar = Bar("Processing files", max=len(files))
        for file in files:
            sql = f"SELECT ARRAY_AGG(model) FROM devices WHERE blobs  @> '[{{\"file\": \"{file[0]}\"}}]';"
            # print(f"SQL: {sql}")
            result = self.dbcursor.execute(sql)
            devs = self.dbcursor.fetchone()
            devices.append({"file": file[0], "devices": devs[0]})
            bar.next()
        bar.finish()
        return devices

def main():
    """This main function lets this class be run standalone by a bash script."""
    choices = ("count", "totals", "sizes", "files", "devices")
    parser = argparse.ArgumentParser(description="Query device data in postgres")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-l", "--list", choices=choices, help="Find device metadata")
    parser.add_argument("-t", "--track", help="Find devices containing file")
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

    totals = dict()
    devdb = QueryDevice()

    if args.track:
        csvfile = open("track.csv", 'a', newline='')
        data = devdb.track_file(column, args.track)
        # log.info(f"{len(data)} devices contain {tmp[1]}")
        totals["images"] = data
        fieldnames = ("file", "models")
        csvout = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvout.writeheader()
        for key, value in totals.items():
            alldevs = str()
            for entry in value:
                alldevs += f"{entry[1]}, "
            out = {"file": tmp[1], "models": alldevs[:-2]}
            csvout.writerow(out)
        log.info(f"Wrote track.csv")

        # log.debug(data)
        quit()

    if args.list:
        if args.list == "devices":
            totals = devdb.list_devices()
            fieldnames = ("file",
                          "count",
                          "devices",
                          )
            csvfile = open(f"{args.list}.csv", 'w', newline='')
            csvout = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvout.writeheader()
            bar = Bar("Writing data...", max=len(totals))
            for entry in totals:
                row = str(entry["devices"])[2:-2]
                csvout.writerow({"file": entry["file"], "count": len(entry["devices"]), "devices": row})
                bar.next()
            bar.finish()
            log.info(f"Wrote {args.list}.csv")
            quit()

        totals = dict()
        if args.list == "sizes":
            totals = devdb.track_size()
            fieldnames = ("vendor",
                          "model",
                          "build",
                          "file",
                          "size",
                          "md5sum",
                          "type",
                          )
            csvfile = open("sizes.csv", 'w', newline='')
            csvout = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvout.writeheader()
            for entry in totals:
                out = {"vendor": entry[0].title(),
                       "model": entry[1],
                       "build": entry[2],
                       "file": entry[3],
                       "size": entry[4],
                       "md5sum": entry[5],
                       "type": entry[6],
                       }
                csvout.writerow(out)
            log.info(f"Wrote sizes.csv")
            quit()

        if args.list == "count":
            csvfile = open("count.csv", 'w', newline='')
            totals = devdb.list_count()
            fieldnames = ("vendor",
                          "model",
                          "build",
                          "total",
                          )
            csvout = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvout.writeheader()
            for entry in totals:
                out = {"vendor": entry[0].title(),
                       "model": entry[1],
                       "build": entry[2],
                       "total": entry[3],
                       }
                csvout.writerow(out)
            log.info(f"Wrote count.csv")
            quit()

        if args.list == "totals":
            csvfile = open("totals.csv", 'w', newline='')
            fieldnames = ('vendor',
                          'model',
                          'build',
                          'type',
                          )
            csvout = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvout.writeheader()
            for val in Bintypes:
                data = devdb.list_totals(val)
                for row in data:
                    device = dict()
                    device["vendor"] = row[0].title()
                    device["model"] = row[1]
                    device["build"] = row[2]
                    device["type"] = row[3]
                    csvout.writerow(device)
            log.info(f"Wrote totals.csv")

        if args.list == "files":
            csvfile = open("files.csv", 'w', newline='')
            fieldnames = ('vendor',
                          'model',
                          'build',
                          )
            fieldnames += columns
            csvout = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvout.writeheader()
            for column in columns:
                result = devdb.list_elements(column)
                # print(result)
                if not result:
                    continue
                for dev in result:
                    if dev[3] is None:
                        continue
                    # data = eval(json.dumps(dev[3]))
                    # data["vendor"] = self
                    allfiles = str()
                    file = dict()
                    for group in dev[3]:
                        for blob in group:
                            allfiles += f"{blob["file"]}, "
                    file["vendor"] = dev[0].title()
                    file["model"] = dev[1]
                    file["build"] = dev[2]
                    file[column] = allfiles[:-2]
                    csvout.writerow(file)
                    # logging.info(f"{dev[0]}, {dev[1]}, {dev[2]}: {allfiles[:-2]}")
            log.info(f"Wrote files.csv")
            quit()


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
