# Getting Device Metadata From Postgres

To assist on querying the postgres database containing device metadata,
there is a script that does standard queries. These all output a CSV
file, so can be loaded into a spreadsheet program for further
analysis for those not experienced with SQL.

## Data Schema

Currently the only metadata stored for each file is the filename, the
size, the file type, and the md5sum. This will be expanded as more
analysis is done.

## Options

	query_dev.py [-h] [-v] [-l {count,sizes,devices}]

	-h, --help                       show this help message and exit
	-v, --verbose                    verbose output
	-l, --list {count,sizes,devices} Extract device metadata
	-t, --track TRACK                Find devices containing file
	-d, --diff build1,build2         Diff blobs between two builds

### --list

This options support several commands, all of which output data into a
CSV files for further analysis.

#### count

This lists all the devices with a count of how many binary files are
in each device.

#### sizes

This contains a list of all the files with their size and md5sum. This
can be used to track variations in the blobs across time and to see
what is shared amongst devices.

#### devices

This contains a list of each file, and the devices that use it.

### --diff

This compares all the blobs between two devices. This is useful when
analyzing firmware between two variations of the same device model.

## [Data Files](csvdata.md)

There are also extracts using these options in CSV format so you don't
even need to run this program.

