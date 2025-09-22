# Importing Device Metadata Into Postgres

To assist in analyzing all the proprietary files, the
*import_device.py* script is used to import information about each
into a postgres database. Currently the metadata on each file is
limited to the file type, the size, and the md5sum, but this will be
expanded.

## File Types

Many of these don't have an offical [magic
number](https://en.wikipedia.org/wiki/Magic_number_(programming)), so
I've been analyzing the usual location for a magic number for patterns
that I have validated to be unique to that type of file, and all files
with that type are use the same number. Since know of these are
official, I maintain my own list of these.

Others that I can't identify a unique magic number for I can often
analyze the filename. Many use a naming convention where the name
starts with the chipset it supports, followed by a version
number. Digging around on the internet for data sheets, I can then
identify the function of the file type, and use that as the file type.

There are also many, many binary data files that aren't executable
files, so I identify those, but mostly ignore them as clutter when
doing data extracts. These are often a data structure used to
configure the running executable, often just configuring it for a
specific version of the chipset.

There are also many media files, sound clips, ringtones, graphic
images, they can also be ignored once identified. The goal is
winnowing down all the files to find just the blobs with executable
files, and identify which devices use them.

## Options

	usage: import-device [-h] [-v] [-i INDIR] [-o OUTDIR] [-f FILE] [-b BOOTSTRAP]

	-h, --help                show this help message and exit
	-v, --verbose             verbose output
	-i, --indir INDIR         The top level vendor directory
	-f, --file FILE           Get data for a file
	-b, --bootstrap           Bootstrap a table with minimal data

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
