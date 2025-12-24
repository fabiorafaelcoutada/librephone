# File Structure

Due to the availability of Lineage install packages, it's possible to
extract all the proprietary files without any hardware.

## Top Level

After unzipping the Lineage package, there are several files, the one
we want is the *payload.bin* file because the Fairphone FP6 is a
payload-based OTA file. Some of the zip files give me an error using
either the *unzip*  program or the Python module. Since we only want
to look at the files, the workaround is to disable the check like
this:

	export UNZIP_DISABLE_ZIPBOMB_DETECTION="TRUE"

For more details on the 3 packaging formats, there's a [good
doc](https://wiki.lineageos.org/extracting_blobs_from_zips_manually)
on the Lineage wiki. To unpack the payload.bin OTA file, Lineage
includes a program called  *ota_extractor*. I use a different propgram
which is faster called
[otadump](https://github.com/crazystylus/otadump). There's also
multiple other OTA extraction programs in github.

At the top level, all the files are packaged as image files. These are
a mix of filesystem images, boot code, and SSL certificates. Older
devices have fewer filesystems. Newer devices have the vendor and
device specific support in separate files, and sometimes split down
even further. The primary filesystems are *system.img*, *product.img*,
*modem.img*, *odm.img*, and vendor.img*. There is often a
*bluetooth.img* file used to store SSL certificates for the
firmware. Sometimes there is a *vendor_dlkm.img* or *system_dlkm.img*,
which contains all of the kernel modules. To extract files from these
images you can mount them to a diretory, so access is easy. 

## The Filesystems

These are the primary top level image files that are mountable file
systems. Sometimes there are multiple vendor and system images, but
they all contain the same files, they're just packaged differently to
make it easier to separate out the vendor and device specific files
from the rest that is for a generic device.

### modem.img

This files contains the bulk of the software used for the radio
subsystem.

#### Hexagon DSP6

The core of the radio subsystem is the Qualcomm Hexagon Digitial
Signal Processor (DSP) chip. These are easily identified. All of the
__adsp.b[0-9][0-9]__ files are for the DSP's Application Processor, and all of
the __cdsp.b[0-9][0-9]__ files are for the DSP Compute Engine.

#### qca6750

This subdirectory contains all of the files specific to the Qualcomm
WCN6750 chip, which is the subsystem used for non-cellular radio
support. This is covered in [more detail here](wireless.md), and
contains the Wireless Processor SubSystem (WPSS) that used for low
level hardware control on the WCN6750. These __wpss.[0-9][0-9]__ files are
not all executables, and the executables are for several CPU cores
like a Cortex-M4 or a RISCV32. The __bdwlan.e[0-9][0-9]__ files are all AARCH32
executables for the "little" core on the SoC.

### system.img


### vendor.img

This contains device specific firmware for non-radio devices like the
fingerprint reader, the camera, the touchscreen. The firmware is in
the *firmware* subdirectory, and all the libraries art in *lib64*.

### bluetooth.img

Most of the bluetooth code is in the *modem.img* image, these are
primarily device customization files. None of these files are loaded
by the kernel, since the core bluetooth code can access them because
they're in a filesystem.

* evrbtfw20.tlv, evrbtfw20.ver, evrnv20.bin
* msbtfw11.mbn, msnv11.bin, msbtfw11.tlv, msbtfw11.ver	
* msbtfw12.tlv,  msnv12.bin, msbtfw12.mbn, msbtfw12.ver
