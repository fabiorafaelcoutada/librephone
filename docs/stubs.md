# Code Stubs

This project uses enums defined to be same for both Python and
Postgresql. While it's possible to do this dynamically in pyscopg2,
this uses a more static version by generating bindings for both Python
and Postgresql for a YAML based config file. This also allows for
future bindings to other languages.

A program called [generator](generator.md) is used to read in the
configuration files and generates the output files. You can run *make*
to regenerate these files if you have changed the YAML files.

Using enums are important to enforce consistent data values which are
needed to get accurate results from SQL queries. Too much flexibiity
can lead to convoluted code and madness...

## Output Files

For each YAML file, a single output file is created. The
*typedefs.yaml* file will generate a *typedefs.py* and a
*typedefs.sql* of all the type definitions. Think of these like a
header file. Type definitions must be loaded first in both Python and
Postgres for the rest to work. To generate the files, do this:

	[path]/generator -v -t typedefs.yaml
	
After generating the typedefs files, you can generate the table
definitions for postgres, and the class definitions for Python. The
Python class matches the table schema, complete with enum support and
default values.

	[path]/generator -v -c tabledefs.yaml

## Typedefs

Typedefs are defined as simply a list of valid values.

	- archtypes:
		- ARM64
		- AARCH64
		- RISCV
		- WE32100
		- XTENSA
		- MIPS
		- DSP

For Postgres they are turned into a type like this:

	DROP TYPE IF EXISTS public.archtypes CASCADE;
	CREATE TYPE public.archtypes AS ENUM (
        'ARM64',
        'AARCH64',
        'RISCV',
        'WE32100',
        'XTENSA',
        'MIPS',
        'DSP'
);

For Python, they are turned into a slightly weird syntax of:

	class Archtypes(Enum):
        ARM64 = 'ARM64'
        AARCH64 = 'AARCH64'
        RISCV = 'RISCV'
        WE32100 = 'WE32100'
        XTENSA = 'XTENSA'
        MIPS = 'MIPS'
        DSP = 'DSP'

Since Postgres returns values from a SELECT as all caps, this lets
Python use the same value instead of converting between enum string
and integer values all the time. By default, the two values are the
same, but you can also redefine the keyword by adding a value in the
YAML file like this:

	class Archtypes(Enum):
        ARM64 = 'Armv8'
		...

## Table & Class Definitions

Table definitions are different, because they have to support multiple
datatypes. Psycopg will convert between the timestamps, jsonb columns,
but not the enums. By prefixing the enums we've defined with
*public.*, they get recognized by postgresql if the typedefs have been
loaded. Some columns are arrays, so that can also be specified.

	- specs:
		- release:
			- timestamp
		- arch:
			- public.archtypes
		- soc:
			- string
		- cpus:
			- string
			- array: true
		- peripherals:
			- string
			- array: true
		- ram:
			- int32,
		- bluetooth:
			- string
		- wifi:
			- public.wifitypes
			- array: true
		- build:
			- string
		- gpu:
			- string
		- network:
			- public.nettypes
			- array: true
		- kernel:
			- float

This will become this SQL definition:

	DROP TABLE IF EXISTS public.specs CASCADE;
	CREATE TABLE public.specs (
        release timestamp without time zone,
        arch public.archtypes,
        soc character varying,
        cpus character varying[],
        peripherals character varying[],
        ram int,
        bluetooth character varying,
        wifi public.wifitypes[],
        build character varying,
        gpu character varying,
        network public.nettypes[],
        kernel float
);

For Python, this becomes a class where all the data fields match the
datatype of the database schema, which is used to store data to insert
into the data base, or use in python after a query. The enums also
have a default value.

	class SpecsTable(object):
		def __init__(self, 
            release: datetime = '2025-09-11 19:06:05.831884', arch: librephone.typedefs.Archtypes =  librephone.typedefs.Archtypes.ARM64, soc: str = None, cpus: str = None, peripherals: str = None, bluetooth: str = None, wifi: librephone.typedefs.Wifitypes =  librephone.typedefs.Wifitypes.A, build: str = None, gpu: str = None, network: librephone.typedefs.Nettypes =  librephone.typedefs.Nettypes.TWOG, kernel: float = None):
            self.data = {'release': release, 'arch': arch, 'soc': soc, 'cpus': cpus, 'peripherals': peripherals, 'bluetooth': bluetooth, 'wifi': wifi, 'build': build, 'gpu': gpu, 'network': network, 'kernel': kernel}
