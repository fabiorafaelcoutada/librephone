# Importing Device Metadata Into Postgres

To assist in analyzing all the proprietary files, the *import-device*
script is used to import information about each into a postgres
database. Currently the metadata on each file is limited to the file
type, the size, and the md5sum, but this will be expanded.

## File Types

Currently only a subset of the files are scanned, but this is easily
extensible. The file determination is currently based on the filename
suffix till more detailed analysis can be done. For example, there are
multiple types of image files, some are filesystem images, the rest
unknown for now. Most of these have no identifiable [magic
number](https://en.wikipedia.org/wiki/List_of_file_signatures).

* images - Files with a *.img* suffix
* binary - Files with a *.bin* suffix
* hex - Files with a *.hex* suffix
* firmware - Files with a *.fw* or *.fw2* suffix

## Options

	usage: import-device [-h] [-v] [-i INDIR] [-o OUTDIR] [-f FILE] [-b BOOTSTRAP]

	-h, --help                show this help message and exit
	-v, --verbose             verbose output
	-i, --indir INDIR         The top level vendor directory
	-f, --file FILE           Get data for a file
	-b, --bootstrap BOOTSTRAP Bootstrap a table with minimal data

### --file FILE

This extracts the metadata of a single file, and is primarily used
during software development.

### --bootstrap FILE

Since the build names used by Lineage are arbitrary, it's useful to be
able to map the unique build names to a device model. The top level
[images_util.sh](images_util.md) script will output a files when
making symbolic links to all the device directories using the build
name. This way a device can be referred to by either the device name or
the build name, which is useful when navigating through the many
devices. By default, the output file is called *devices.list*. This
option will read in the output file and bootstrap the database with
the vendor, device model, and Lineage build name.

### --indir DIR

This is the top level directory containing the files extracted from
the Lineage packages. This requires the file directory structure to
use the format produced by the [extractor](extractor.md) program. That
structure is simply:

	outdir
	    -> vendor 
	         -> build
