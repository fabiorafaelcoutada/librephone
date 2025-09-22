#!/usr/bin/python3

# Copyright (c) 2025 Free Software Foundation, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import logging
import sys
import os
from sys import argv
from pathlib import Path
# import types_tm
from librephone.yamlfile import YamlFile
# import librephone.typedefs
from datetime import datetime
from shapely.geometry import Point, LineString, Polygon
from librephone.device import DeviceData
from librephone.typedefs import Cputypes, Gpumodels, Devstatus, Imgtypes, Bintypes, Archtypes, Celltypes, Nettypes, Wifitypes, Filetypes, Blobtypes

import librephone as pt
rootdir = pt.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

class Generator(object):
    def __init__(self,
                filespec: str = None,
                ):
        """
        A class that generates the output files from the config data.

        Args:
            filespec (str): The config file to use as source.

        Returns:
            (Generator): An instance of this class
        """
        self.filespec = None
        self.yaml = None
        if filespec:
            self.filespec = Path(filespec)
            self.yaml = YamlFile(filespec)
        self.createTypes()
        self.yaml2py = {'int32': 'int',
                    'int64': 'int',
                    'float': 'float',
                    'double': 'float',
                    'bool': 'bool',
                    'string': 'str',
                    'bytes': 'bytes',
                    'timestamp': 'timestamp without time zone',
                    'polygon': 'Polygon',
                    'point': 'Point',
                    'jsonb': 'dict',
                    }

        self.yaml2sql = {'int32': 'int',
                    'int64': 'bigint',
                    'bool': 'bool',
                    'string': 'character varying',
                    'bytes': 'bytea',
                    'timestamp': 'timestamp without time zone',
                    'polygon': 'geometry(Polygon,4326)',
                    'point': 'geometry(Point,4326)',
                    'jsonb': 'jsonb',
                    'float': 'float',
                    'double': 'float',
                    }        

    def readConfig(self,
                    filespec: str,
                    ):
        """
        Reads in the YAML config file.

        Args:
            filespec (str): The config file to use as source.
        """
        self.filespec = Path(filespec)
        self.yaml = YamlFile(filespec)

    def createTypes(self):
        """
        Creates the enum files, which need to be done first, since the
        other generated files reference these.
        """
        gen = self.readConfig(f'{rootdir}/typedefs.yaml')
        out = self.createSQLEnums()
        with open('typedefs.sql', 'w') as file:
            file.write(out)
            file.close()
        out = self.createPyEnums()
        with open('typedefs.py', 'w') as file:
            file.write(out)
            file.close()

    def createSQLEnums(self):
        """
        Create an input file for postgres of the custom types.

        Returns:
            (str): The source for postgres to create the SQL types.
        """
        out = ""
        for entry in self.yaml.yaml:
            [[table, values]] = entry.items()
            out += f"DROP TYPE IF EXISTS public.{table} CASCADE;\n"
            out += f"CREATE TYPE public.{table} AS ENUM (\n"
            for line in values:
                if type(line) == dict:
                    [[k, v]] = line.items()
                    breakpoint()
                    out += f"\t'{k}',\n"
                else:
                    out += f"\t'{line}',\n"
            out = out[:-2]
            out += "\n);\n"
        return out

    def createPyEnums(self):
        """
        Create an input file for python of the custom types.

        Returns:
            (str): The source for python to create the enums.
        """
        out = f"import logging\n"
        out += f"from enum import Enum\n"
        for entry in self.yaml.yaml:
            index = 1
            [[table, values]] = entry.items()
            out += f"class {table.capitalize()}(Enum):\n"
            for line in values:
                # breakpoint()
                if type(line) == dict:
                    [[k, v]] = line.items()
                    out += f"\t{k} = '{v}'\n"
                else:
                    # out += f"\t{line} = {index}\n"
                    out += f"\t{line} = '{line}'\n"
                index += 1
            out += '\n'
        return out

    def createSQLTable(self):
        """
        Create the source for an SQL table.

        Returns:
            (str): The protobuf message source.
        """
        out = "-- Do not edit this file, it's generated from the yaml file\n\n"
        sequence = list()
        primary = list()
        partition = list()
        for entry in self.yaml.yaml:
            [[table, values]] = entry.items()
            out += f"DROP TABLE IF EXISTS public.{table} CASCADE;\n"
            out += f"CREATE TABLE public.{table} (\n"
            unique = list()
            typedef = ""
            for line in values:
                # these are usually from the types.yaml file, which have no
                # settings beyond the enum value.
                if type(line) == str:
                    # print(f"SQL TABLE: {typedef} {line}")
                    typedef = table
                    continue
                [[k, v]] = line.items()
                required = ""
                array = ""
                public = False
                primary = list()
                partition = list()
                for item in v:
                    if type(item) == dict:
                        if 'sequence' in item and item['sequence']:
                            sequence.append(k)
                        if 'required' in item and item['required']:
                            required = ' NOT NULL'
                        if 'array' in item and item['array']:
                            array = "[]"
                        if 'unique' in item and item['unique']:
                            unique.append(k)
                        if 'primary' in item and item['primary']:
                            primary.append(k)
                        if 'partition' in item and item['partition']:
                            partition.append(k)
                    if len(v) >= 2:
                        if 'required' in v[1] and v[1]['required']:
                            required = ' NOT NULL'
                    if type(item) == str:
                        if item[:7] == 'public.' and item[15:8] != 'geometry':
                            public = True
                        # elif item[15:8] == 'geometry':
                        #     out += f"\t{k} {self.yaml2py[v[0]]}{array}{required},\n"
                if public:
                    out += f"\t{k} {v[0]}{array}{required},\n"
                else:
                    # print(v)
                    # FIXME: if this produces an error, check the yaml file as this
                    # usually means the type field isn't first in the list.
                    if v[0][:6] == 'table.':
                        out += f"\t{k} {v[0][6:]}{array},\n"
                    else:
                        try:
                            out += f"\t{k} {self.yaml2sql[v[0].replace(',', '')]}{array}{required},\n"
                        except:
                            breakpoint()
            if len(unique) > 0:
                keys = str(unique).replace("'", "")[1:-1];
                out += f"\tUNIQUE({keys})\n);\n"
            if out[-2:] == ',\n':
                out = f"{out[:-2]}\n);\n\n"
            if len(sequence) > 0:
                for key in sequence:
                    out += f"""
DROP SEQUENCE IF EXISTS public.{table}_{key}_seq CASCADE;
CREATE SEQUENCE public.{table}_{key}_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;

"""
        if len(primary) > 0:
            keys = str(primary).replace("'", "")[1:-1];
            out += f"\tALTER TABLE {table} ADD CONSTRAINT {table}_pkey PRIMARY KEY({keys})\n);\n"

        return out + "\n"

    def createPyClass(self):
        """
        Creates a python class wrapper for the protobuf messages.

        Returns:
            (str): The source for python to create the class stubs.
        """
        out = f"""
import logging
from datetime import datetime
import librephone.typedefs
from shapely.geometry import Point, LineString, Polygon

log = logging.getLogger(__name__)

        """
        for entry in self.yaml.yaml:
            [[table, settings]] = entry.items()
            out += f"""
class {table.capitalize()}Table(object):
    def __init__(self,
            """
            datatype = None
            now = datetime.now()
            data = "            self.data = {"
            breakpoint()
            for item in settings:
                if type(item) == dict:
                    [[k, v]] = item.items()
                    for k1 in v:
                        if type(k1) == dict:
                            continue
                        elif type(k1) == str:
                            if k1[:15] == 'public.geometry':
                                datatype = k1[16:-1].split(',')[0]
                                log.warning(f"GEOMETRY: {datatype}")
                            elif k1[:7] == 'public.':
                                datatype = f"librephone.typesdefs.{k1[7:].capitalize()}"
                                # log.warning(f"SQL ENUM {k1}! {datatype}")
                            elif k1 in self.yaml2py:
                                datatype = self.yaml2py[k1]
                            else:
                                datatype = item
                                continue
                        if k1 == 'bool':
                            out += f"{k}: {datatype} = False, "
                        elif k1 == 'timestamp':
                            out += f"{k}: datetime = '{datetime.now()}', "
                        elif k1[:7] == 'public.':
                             #defined = f"librephone.typedefs.{k1[7:].capitalize()}"
                            # log.warning(f"SQL ENUM {k1}!!")
                            # default = eval(f"{defined}(1)")
                            #out += f"{k}: {defined} =  {defined}.{default.name.upper()}, "
                            pass
                        else:
                            out += f"{k}: {datatype} = None, "
                        # print(k)
                        data += f"'{k}': {k}, "
            out = out[:-2]
            out += "):\n"
            out += f"{data[:-2]}}}\n"

        return out

def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(
        prog="generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Generate SQL and Python data structures",
        epilog="""
        This should only be run standalone for debugging purposes.
        """,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-t", "--typedefs", help="Generate Typedefs")
    parser.add_argument("-c", "--classes", help="Generate tables and classes")
    args = parser.parse_args()

    if len(argv) <= 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    log_level = os.getenv("LOG_LEVEL", default="INFO")
    if args.verbose is not None:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s.%(msecs)03d [%(levelname)s] " "%(name)s | %(funcName)s:%(lineno)d | %(message)s"),
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    gen = Generator()
    if args.typedefs:
        gen.readConfig("typedefs.yaml")
        out = gen.createTypes()

    if args.classes:
        gen.readConfig("tabledefs.yaml")
        out = gen.createSQLTable()
        with open('tabledefs.sql', 'w') as file:
            file.write(out)
            file.close()
        out = gen.createPyClass()
        with open('tabledefs.py', 'w') as file:
            file.write(out)
            file.close()

if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
