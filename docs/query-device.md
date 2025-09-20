# Getting Device Metadata From Postgres

To assist on querying the postgres database containing device metadata,
there is a script that does standard queries. These all output a CSV
file, so can be loaded into a spreadsheet program for further
analysis for those not experienced with SQL.

Currently only a subset of the file types are scanned, but this is easily
extensible. The file type determination is currently based on the
filename suffix till more detailed analysis can be done. For example,
there are multiple types of image files, some are filesystem images,
the rest unknown for now. Most of these have no identifiable [magic
number](https://en.wikipedia.org/wiki/List_of_file_signatures).

The file types we're interested in are:

* images - Files with a *.img* suffix
* binary - Files with a *.bin* suffix
* hex - Files with a *.hex* suffix
* firmware - Files with a *.fw* or *.fw2* suffix

## Data Schema

Currently the only metadata stored for each file is the filename, the
size, the file type, and the md5sum. This will be expanded as more
analysis is done.

## Options

usage: query-device [-h] [-v] [-l {count,sort=list}]

options:

	-h, --help                   Show this help message and exit
	-v, --verbose         	     Verbose output
	-l, --list {count,sort=list} List device metadata

### --list

This options support several commands, all of which list data in CSV
format

#### count

This lists all the devices with a count of how many files are in each
file type category.

#### sort=list

This lists all the devices with a list of all the file names in each
category instead of just a count of entries.
