# Wifi & Bluetooth Support

The [Qualcomm
wcn6750](https://www.qualcomm.com/wi-fi/products/fastconnect/fastconnect-6700)
chipset is used for wifi support when coupled with a SnapDragon
SoC. Since datasheets and most all documentation requires an NDA with
Qualcomm, about the only decent doc is the Linux [kernel
patch](https://lwn.net/Articles/889433/) that adds wcn6750
support. This uses the atk11k device driver, which supports several
other chipsets.

This chip appears to have an embedded ARM core, and possibly a RISCV
core as well. These blobs are in the *modem.img* file, and are in the
*modem/image/qca6750* directory. On a device, they're in the
*/vendor/firmware_mnt/image/qca6750/* directory.

## Tools

A variety of open source tools have been used to attempt to identify
all the files. This includes the [GNU
Binutils](https://www.gnu.org/software/binutils/),
[Binwalk](https://github.com/ReFirmLabs/binwalk),
[Cutter](https://cutter.re/), and
[Ghidra](https://ghidra-sre.org/). While the Unix *file* utility can
identify some of the blobs, for most of these files it only sees them
as data.

## QCA6750 Blobs

The higher level blobs use the WPSS to control the hardware. There are
three types of blobs. There are many files with the pattern
*bdwlan.b[0-9][0-9]* which are Board Device Files (BDF) used to
customize the software for a particular chipset. Only one is used, so
the rest can be ignored. The active file gets compiled into a
*bdwlan.bin* file. The only file loaded at boot time is *bdwlan.elf*,
which is a 32 bit AARCH32 file.

In addition, there are also many files with the pattern
*bdwlan.e[0-9][0-9]*, which are 32bit AARCH32 files. Since they aren't
loaded at boot time, I assume the bdwlan.elf code loads at least one
of these blobs. It may load all of them, but because they are all the
same size, I think like the __bdwlan.b*__ files, these are each device
specific.

## Wireless Processor SubSystem (WPSS)

This is the firmware that used for wifi & bluetooth support. It
includes the baseband digital signal processing, an RF transceiver, and
power amplifier. It contains an ARM Cortex-M3 or M4 core for
application code. It looks like it also contains a RISCV core. The
blob that seems to be an Intel x86_32 is suspicious.

* wpss.b00 - ELF 32-bit LSB executable, QUALCOMM DSP6
* wpss.b01 - ATMel AVR 8 Cortex-M little endian
* wpss.b02 - ELF64, little endian AARCH64 binary
* wpss.b03 - ELF64, little endian AARCH64 binary
* wpss.b04 - ELF64, little endian AARCH64 binary
* wpss.b05 - ELF64 little endian relocatable, AARCH64
* wpss.b06 - looks like boot code and contains multiple files
* wpss.b07 - ELF32 little endian RISCV32 binary
* wpss.b08 - ELF32 little endian Intel i386 binary
* wpss.b09 - 64 bit little AARCH64 binary

## The Software Stack

There are several layers of software used to interface with the
firmware. All of the source code for these layers are part of the
Qualcomm opensource release. The architecture of the wireless software
stack is explained in detail [in this
document](https://deepwiki.com/TechNexion/qcacld-2.0/1-overview), so
this is just a quick summary.

### [Host Device Driver (HDD)](https://deepwiki.com/TechNexion/qcacld-2.0/2-host-device-driver-(hdd)#host-device-driver-hdd)

This is the primary interface between the kernel's networking stack
and the driver.

### [Station Management Entity (SME)](https://deepwiki.com/TechNexion/qcacld-2.0/1.1-system-architecture#station-management-entity-sme)

This is the interface between the HDD and the protocol engine.

## [Wireless Module Interface (WMI)](https://deepwiki.com/TechNexion/qcacld-2.0/5.1-wireless-module-interface-(wmi)#wmi-architecture)

This is commnd and event protocol used between the driver and the firmware.

### [Wireless Management Agent (WMA)](https://deepwiki.com/TechNexion/qcacld-2.0/5-wireless-management-agent-(wma)#wireless-management-agent-wma)

This is the interface between the SME and the WMI.

## [Hardware Interface (HIF)](https://deepwiki.com/TechNexion/qcacld-2.0/1-overview#hardware-interface-hif)

This interfaces with the actual hardware.


