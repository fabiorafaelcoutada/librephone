# Data Files

Since I have a fully populated database, and not everyone wants to run
a full database I've included a few dumps from the database

## [devices.csv](https://codeberg.org/rsavoye/librephone/src/branch/main/data/devices.csv)

This contains a list of each file, and the devices that use it.

## [count.csv](https://codeberg.org/rsavoye/librephone/src/branch/main/data/count.csv)

This lists all the devices with a count of how many binary files are
in each device.

## [sizes.csv](https://codeberg.org/rsavoye/librephone/src/branch/main/data/sizes.csv)

This contains a list of all the files with their size and md5sum. This
can be used to track variations in the blobs across time and to see
what is shared amongst devices.

## [devices.sql.bz2](https://codeberg.org/rsavoye/librephone/src/branch/main/data/devices.sql.bz2)

This is a large file containing a dump of a fully populated
database. This will let other developers write their own SQL queries
if they are running Postgres.
