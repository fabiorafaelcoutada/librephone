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

import pandas as pd
import argparse
import sys
from sys import argv
import logging


def main():
    """This main function lets this class be run standalone by a bash script."""
    choices = ("count", "sort=list")
    parser = argparse.ArgumentParser(description="Query device data in postgres")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", help="The CSV file to convert")
    parser.add_argument("-o", "--outfile", help="The optional output name")

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

    if args.infile:
        if not args.outfile:
            outfile = args.infile.replace(".csv", ".md")
        df = pd.read_csv(args.infile, engine='python')
        with open(outfile, 'w') as md:
            df.fillna('', inplace=True)
            df.to_markdown(buf=md, index=False)
        
if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
