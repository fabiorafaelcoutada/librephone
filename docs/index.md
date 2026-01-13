# librephone Project

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

## Lineage Packages

- [Comparing Devices](comparing.md) This describes the process of
analyzing all the binary blobs in the devices supported by Lineage.

- [File Structure](files.md) This describes the top level blobs found
in a Lineage package.

## Technical Details

- [Tools](tools.md) This covers all the free and open source tools I
use for reverse engineering.

- [AARCH32 Thumb Mode](thumb.md) This covers how to dissasemble
AARCH32, which supports 2 instruction sets.

- [WPSS](wireless.md) This describes the Wireless Processor SubSystem.

## Utility Programs

This project contains [several utilities](utilities.md) for analyzing
proprietary files and binary blobs in Android. They are oriented
towards any developers wishing to duplicate the research on their
own. If you want to use these, chances are you might have to edit a
few paths.

These utilities require you have download the Lineage install package
for the devices you are interested in researching. There is also a top
level script [images_util.sh](images_util.md) that can automate
the processing of multiple devices.

- [extractor.py](extractor.md) This is a simple utility to unpack and
mount the system files from the Lineage packaged installer file.

- [import_dev.py](import-device.md) Import data on all proprietary
files and binary blobs into a database so they can be better analyzed.

- [query_dev.py](query-device.md) This script does common SQL queries
and dumps them as CSV file.

- [generator.py](generator.md) This program uses a YAML config file to
generate bindings for Python or Postgres.

	- [Code Stubs](stubs.md) This documents the format of the config files
for the generator.

- [images_util.sh](images_util.md) This is only for developers who
want to reproduce the research by analyzing the multiple devices
supported by Lineage.

### [Data Files](csvdata.md)

These are extracts from the database produced by the
*query_devices.py* program in CSV format. These can be further
analyzed by using a spreadsheet program.

