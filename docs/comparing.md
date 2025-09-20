# Comparing Devices

In order to be able to compare the devices Lineage supports, It's
necessary to use the Lineage install packages if you don't have the
device hardware. These zip files contain the proprietary files
copied off an actual device. To compare multiple devices required
manually downloading all the install zip files from the Lineage
website (210 of them). These are all large files, over a gigabyte, so
lots of disk space is needed. In a parallel directory of the Lineage
sources, all the images are stored organized by vendor & model. For
example, my directory tree looks like this:

	images/
		/google
			Pixel_7a
			Pixel_9_Pro
			...
		/motorola/
			Moto_G5
			Edge_40
		...
	Lineage-22.2
		.repo
		device
		vendor
		...

There are multiple steps required to successfully extract the
proprietary files from the zip packages and have Lineage build all the
way to an installable image. First Lineage must be configured for the
device using the *breakfast* command. That does a partial install of
the vendor and model specific files. This step downloads the model
specific kernel sources, so takes a while.

Once that is done, there is a newly created directory for the device
files. It's in this directory where the Lineage program that copies
the proprietary files into Lineage gets run. If that succeeds, then
*breakfast* is run again to complete installing the vendor specific
files. Then you can compile Lineage if all of this has worked.

## Package Formats

There are 3 primary types of packages, These are covered in more
detail on the [Lineage
Wiki](https://wiki.lineageos.org/extracting_blobs_from_zips), but
here's a short summary.

### Payload

The system partition is in the payload.bin file. This seems to be
the most common format.

### File

The system partition is in a zip file. Note, haven't seen any of these
yet.

### Block

The system partition is in a *.dat* or a *.dt.br* file. This is only
used by a few, like Xiaomi and Samsung.

## [extractor.py](extractor.md)

This project contains a script to handle de-packaging the Lineage
install files. In order to extract the proprietary files from the
Lineage install packages, first it gets unzipped. That creates a
handful of files, mostly system images or configuration data.
The files in the zip are in different packaging formats, so need to be
further processed before Lineage can use them. Most of the files in
the zip package are filesystem images. When extracting files, Lineage
mounts the filesystem, to access the files.

If you have multiple zip file versions, use the *-z* option, otherwise
it'll default to the current Lineage release. When done, the directory
will be populated by all of the files Lineage needs to try to extract
the proprietary files.

### Payload Format

After unzipping, there is a *payload.bin* and a
*payload_properties.txt* file. These use the
[otadump](https://github.com/crazystylus/otadump) program. The output
of this program are the final filesystem images.

### Block Format

Block Format use data files to create the the filesystem images. The
files are compressed using brotli, which is available for most
operating systems. After unzipping there are several files
__*.transfer.list__, __*.patch.dat__, and __*.data.br__ files for the
primary types. Those are *odm*, *product*, *system*, *system_ext*, and
*vendor*.

The [sdat2img-brotli](https://pypi.org/project/sdat2img-brotli)
program reads in the data files and the transfer.list files and
produces the file system images. Each filesystem uses the type for the
filename, so *system.dat*, *system.new.dat.br*, and
*system.transfer.list* generates *system.img*.

## [images_util.sh](images_util.md)

This shell script automates the process of working through all 210
devices. It does all the steps of configuring, extracting files, and
building Lineage for multiple devices. This requires the Lineage zip
files to be in the vendor/model directory tree of images from Lineage
install packages. Currently this script defaults to the latest Lineage
release of 22.2, but this can easily be changed in the top of the
file. Much of the file processing works without Lineage, and Lineage
also uses the extracted files to build for a device.

When building Lineage, much of the time is spent downloading device
specific code like the kernel source for each device which may be over
gigabyte, so not fast. It is possible to download all the vendor and
device data, but if you try to build Lineage you get a dependency
problem, so have to delete the vendor directories from the vendor and
device directories (maybe run repo sync if there are problems)

Command line options are:

	--help (-h):    Display help screen
	--dryrun (-d):  Just dry run,don't execute anything
	--remove (-r):  Remove all generated files
	--link (-l):    Link build names to device name
	--extract (-e): Extract files from package
	--clone (-c):   Clone files
	--unmount (-u): Unmount all device file-systems
	--build (-b):   Build packages
	--import (-i):  Import blobs into a database
	--all (-a):     Do everything, which takes a long time

Note that since this program processes close to 210 Lineage packages,
it may take a considerable amount of time to finish, and expect bugs
in some of the packages for some of the devices.

## Lineage Extraction Scripts

Up until Lineage 22.1 a shell script was previously used to extract
files. As of the 22.2 release, most devices have been converted to the
new python based scripts. Lineage contains a template for this script
which is copied to the device sub-directory in Lineage. Both scripts
read the same configuration files, but if you try to build a device
that does not contain the python version, it probably will fail with
the packages and you'll have to use the actual hardware.

For each device, the forked *extract-files.py* script is customized
for any device specific file manipulation like applying
patches. Most of the work is done by Lineage python modules, so these
scripts are primarily calling functions shared across all devices.

## Extraction Scripts

The purpose of this project is researching the proprietary files,
and not building Lineage directly. By using the same config files
Lineage uses, we can extract everything, Lineage needs, but set up for
analysis instead. Differences between the files listed in the Lineage
config files and the install package are logged for further
analysis. The [extractor](extractor.md) script doesn't download the
kernel sources since we're not compiling Lineage, so much faster if
all you want to do is extract the proprietary files.

These scripts all take a directory with the zip file as an argument
making it easy to automate. Do to this manually for a specific
directory requires a few steps. First unzip the install package, then
extract the proprietary files from the filesystem images.

	extractor -v --unzip [path]/motorola/nio
	extractor -v --extract [path]/motorola/nio
	extractor -v --mount  [path]/motorola/nio
	extractor -v --clone  [path]/motorola/nio
	extractor -v --remove [path]/motorola/nio

The [images_util.sh](images_util.md) script does all of these steps
for all supported devices, so is the best way to process the
data. Doing it manually is just for development when working on a
specific device.

###  The Configuration files

These are the 4 files used for extracting the proprietary files. These
text files are just a list of the files to copy off a hardware device,
or from the packaged zip files.

* proprietary-files-carriersettings.txt
* proprietary-files-vendor.txt
* proprietary-firmware.txt
* proprietary-files.txt

The extract-files.py script also have a command line option to
regenerate these lists of files from a hardware device, but not from
the zip packages. In some cases these lists are out of sync with the
Lineage install packages, so don't work without a little debugging.

These files also don't exist unless you have run the *breakfast*
command to build for a device. In that case, the extractor program
mounts and scans for the proprietary files and generates a new
proprietary-files.txt file. That can be used to extract all the
files we want without downloading the kernel source for each one.

## Importing Into Postgres

Once all the proprietary files we care about are cloned to an output
directory, metadata on each file can be imported using the
[import-device](import-device.md] program in this project into a
postgres database. While the database can be queried directly, there
is a [query-device](query-device.md) program with a few canned
queries. Each query produces a CSV file so can be opened in a
spreadsheet program for more analysis.

### Current Metadata

Since this project is in it's early stages, the metadata on each is
limited to the size, type, and md5sum of each file. Each device entry
in the database uses JSONB columns, so can be extended as more data on
each file is collected.
