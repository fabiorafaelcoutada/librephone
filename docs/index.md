# Phone Tools Project

This is a project to research proprietary files in Android to work
towards a long-term goal of free replacements. While there are many
proprietary libraries and other files in Android, this project is
focused on [binary
blobs](https://en.wikipedia.org/wiki/Binary_blob). Initially the
research is focused on identifying the best device for software
development. And also documenting how the blobs get used by the kernel
as a guide to what it would take to
[clean-room](https://en.wikipedia.org/wiki/Clean-room_design) legally
reverse engineer them.

If there is sufficient interest and funding, a detailed specification
can be written and used to have somebody code a free implementation
that works the same way.

## Utility Programs

This project contains several utilities for analyzing proprietary
files and binary blobs in Android. They are oriented towards any
developers wishing to duplicate the research on their own. If you want
to use these, chances are you might have to edit a few paths.

These utilities require you have download the Lineage install package
for the devices you are interested in researching. There is also a top
level script [images_util.sh](docs/images_util.md) that can automate
the processing of multiple devices.

### [extractor.py](extractor.md)

This is a simple utility to unpack and mount the system files from the
Lineage packaged installer file. This is used when using the package
files to extract proprietary files when you don't have hardware. It
handles unpacking everything, and mounting the partitions Lineage
needs to extract files for a device. Extracting is still done using
the extract-files.py script in Lineage for each device.

### [import_dev.py](import-device.md)

Import data on all proprietary files and binary blobs into a database
so they can be better analyzed. This allows one to query which blobs
and files are used by multiple devices.

### [query_dev.py](query-device.md)

This script does common SQL queries and dumps them as
[CSV](https://en.wikipedia.org/wiki/Comma-separated_values) files for
further analysis using a spreadsheet program. It uses a mix of SQL and
python with a focus on being simple to extend for other less common
queries.

