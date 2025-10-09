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

## Utility Programs

This project contains several utilities for analyzing proprietary
files and binary blobs in Android. They are oriented towards any
developers wishing to duplicate the research on their own. If you want
to use these, chances are you might have to edit a few paths.

These utilities require you have download the Lineage install package
for the devices you are interested in researching. There is also a top
level script [images_util.sh](docs/images_util.md) that can automate
the processing of multiple devices.

For more information, the project documentation [is here](docs/index.md).

There's an initial IRC channel at irc.libera.chat:6697,
#librephone. Please join the community!

