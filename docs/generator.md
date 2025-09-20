# generator.py

This project uses enums defined to be same for both Python and
Postgresql. While it's possible to do this dynamically in pyscopg,
this uses a more static version by generating bindings for both Python
and Postgresql for a YAML based config file. This also allows for
future bindings to other languages. The is more detail on the stubs
[here](stubs.md).

As the current version of the generated files are already in git, you
only need to regenerate after changing the YAML files.

## Options

	-h, --help              show this help message and exit
	-v, --verbose           verbose output
	-t, --typedefs TYPEDEFS Generate Typedefs
	-c, --classes CLASSES   Generate tables and classes
