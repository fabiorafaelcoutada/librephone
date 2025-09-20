# Extractor

Extractor is a utility for working with Lineage install
packages. These packages contain all the proprietary files used for
device support. Since we don't have access to all the devices, this
gives us a way to extract the same files for analysis.

All of the files we want are in a zip file. So extractor starts by
unzipping the file to get to the binary files. Then the binary files
are unpacked using either
[otadump](https://github.com/crazystylus/otadump) or
[sdat2img-brotli](https://pypi.org/project/sdat2img-brotli/) 
to extract the filesystem images. These images can then be mounted to
access the files.

The Lineage **extract-files.py** utility doesn't use the mounted
file-systems, it handles that itself. So if you have mounted the
file-systems, you want to unmount them before running
**extract-files.py**.

## Options

By default, extractor does nothing unless an action is supplied.

   	    -h, --help            show this help message and exit
	    -v, --verbose         verbose output
	    -i, --indir INDIR     The top level device directory
	    -z, --unzip [UNZIP]   Decompress the zip file
	    -e, --extract EXTRACT Extract all unzipped files
	    -m, --mount MOUNT     Mount all file-systems
	    -u, --unmount UNMOUNT  Unmount all file-systems
	    -r, --remove REMOVE   Clean all generated file
	    -o, --outdir OUTDIR   The output directory
	    -c, --clone CLONE     Copy the proprietary files for analysis

### --indir

This is the top level directory containing all of the downloaded
Lineage packages, and defaults to the current directory.

### --unzip

This decompresses the Lineage install package into the payload files.

### --mount

This mounts all the filesystem images that have been extracted from
the payload files.

### --unmount

This unmounts all the filesystem images that have been extracted from
the payload files.

### --extract

This uses the Lineage *extract-files.py* script to try to extract all
the proprietary files. Since each device extracts files differently,
this may not work for all devices.

### --clone

This uses the same configuration files Lineage does and extracts all
the listed files into an output directory for further analysis.

### --outdir

This is the output directory used when cloning the proprietary files,
and defaults to *./blobs* if not specified.

### --remove

This removes all generated files leaving only the Lineage zip
package.
