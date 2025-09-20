# Analyzing All Devices

The *images_util.sh* is a simple utility used for maintaining a large
collection of Lineage install packages. These are used to research the
binary blobs for each device. This uses the
[extractor.py](extractor.md) script to do all the work. This script
gets run at the top level to process each device sequentially.

For the Lineage 22.2 release, there are 210 packages. I use this
script frequently, but your mileage may vary... you'll probably
need to to edit a few paths for your system.

# Package Cache

All the packages have been downloaded from Lineage, for the 22.2
release there are 210 supported devices. My cache has a directory
structure like this:

	images/
		/google
			Pixel_7a (linked to by lynx)
			Pixel_9_Pro (linked to by caiman)
			...
		/motorola/
			Moto_G5 (linked to by rhode)
			Edge_40 (linked to by rtwo)
		...

Under each device is the Lineage install zip files for the 22.2 and
22.1 releases. To make it easier to refer to a device by it's build, I
create a symbolic link from the Lineage build name to the device
name. To do this for all packages you can create the links this way:

	[path]/image_utils.sh -l

Since there is no way to get the device model from the Lineage build,
this also produces a config file called *devices.list* which can be
used to bootstrap the database with this binding which simplifies
later SQL queries by be able to relate a Lineage build with a
device. This file also gets used by the other functions in the
*image_utils.sh* utility instead of having each function scan for the
Lineage zip files, with the advantage of making the code faster and
more readable.

	[path]/[import-device](import-device.md) -v -b devices.list

## Options

	--help (-h):    Display this help screen
   	--dryrun (-d):  Just dry run,don't execute anything
   	--remove (-r):  Remove all generated files
   	--link (-l):    Link build names to device name
   	--extract (-e): Extract files from package
   	--clone (-c):   Clone files
   	--unmount (-u): Unmount all device file-systems
   	--build (-b):   Build packages
   	--import (-i):  Import blobs into a database
   	-all (-a):      Do everything, which takes a long time

All of these options are just a wrapper used to process all 210
devices. The extractor script does all of the actual work. This makes
it easy to rescan all the files as more analysis of each file is
implemented.

### --remove

Extracting files from the Lineage install packages generates many
files and sub-directories. This option unmounts any mounted
directories, and then remove all the files except the Lineage zip
file.

#### --link

Traverse the directories containing Lineage install packages and link
the Lineage build name to the device name to make it easy to navigate.

### extract

Extract the files from the Lineage packages, which are filesystem
images. This doesn't mount the filesystem, it only extracts the top
level files.

### clone

If the filesystem images have been extracted from the payload
files. this will mount them and extract all the files listed in the
proprietary-*files.txt files in Lineage. This clones all the files to
the output directories ready to be imported into postgres. This is
required before importing.

### build

The uses the Lineage way of extracting files, so main fail some for
some devices. If the extraction succeeds, it builds an install
package. This may run for s very long time, use ccache to speed up
recompiling.

### import

Imports the metadata on all the devices from the cloned files into a
postgres database. This assumes you are using the output of cloning
using extractor. This also assume you have boot strapped the database
with the *devices.list file*.
