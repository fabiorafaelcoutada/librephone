# WiFi & Bluetooth Support

This document covers analyzing the [binary blobs]() that control a
device's non cellular radio systems, WiFi, Bluetooth, and NFC. Since
there is a lot of variety across devices, this is focused on the
files in a [Fairphone
FP6](https://en.wikipedia.org/wiki/Fairphone_6). Much of this research
can be applied to other devices though.

## The Wireless Chipset

The [Qualcomm
wcn6750](https://www.qualcomm.com/wi-fi/products/fastconnect/fastconnect-6700)
chipset is used for WiFi support when coupled with a SnapDragon
SoC. Since datasheets and most all documentation requires an NDA with
Qualcomm, about the only decent doc is the Linux [kernel
patch](https://lwn.net/Articles/889433/) that adds wcn6750
support. This uses the [atk11k device
driver](https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath11k/installation.html),
which supports several other chipsets which can be ignored.

This chip appears to have an embedded 32 bit ARM core, and possibly a
RISCV32 core as well. These blobs are in the *modem.img* file, and are
in the
[modem/image/qca6750](https://librephone.fsf.org/blobs/FP6/modem/image/qca6750/)
directory. On a device, they're in the
*/vendor/firmware_mnt/image/qca6750/* directory.

## Tools

A variety of open source tools have been used to attempt to identify
all the files. Most of the fancy GUI based reverse engineering tools
use the the [GNU Binutils](https://www.gnu.org/software/binutils/) in
the backend. This includes *nm* for listing symbols (if any exist) and
*objdump* which can disassemble the ELF files into assembly code. The
fancier programs like [Cutter](https://cutter.re/), and
[Ghidra](https://ghidra-sre.org/) often combine what would be multiple
steps in a terminal and sometimes bring in extra tools, like a *decompiler*.

Another tool I use frequently for unpacking blobs is
[Binwalk](https://github.com/ReFirmLabs/binwalk), and occasionally use
[unblob](https://unblob.org/) for the same function. The process of
unpacking the files is [documented here](files.md). The Unix *file*
utility can identify some of the blobs, for most of these it
only sees them as just binary data. When trying to identify a binary
blob, the various programs sometimes disagree on what they think the
blob is. When they agree I assume that's probably accurate. I then
attempt to disassemble them for the identified architecture, not so
much to understand the code, but to see if it's actual assembly code,
or just gibberish that looks like real code.

## QCA6750 Blobs

The higher level blobs use the [WPSS]() to control the hardware. There are
three types of blobs. There are many files with the pattern
*bdwlan.b[0-9][0-9]* which are Board Device Files (BDF) used to
customize the software for a particular chipset. Only one is used, so
the rest can be ignored. The active file gets compiled into a
*bdwlan.bin* file. The only file loaded at boot time is *bdwlan.elf*,
which is a 32 bit AARCH32 file. The format of the BDF files is unknown
as the only documentation available from Qualcomm requires an NDA.

I did find an [open source
program](https://github.com/testuser7/ath_bdf_tool) that reads older
versions of the Atk11k BDF files, but fails to decode the current
version of the BDF files in the FP6. It could be updated for the
current version. The difference appears to be in older BDF files the
*regdb* data is in the BDF file, and in newer versions it's now a
separate regdb.bin file.

In addition, there are also many files with the pattern
*bdwlan.e[0-9][0-9]*, which are 32bit AARCH32 files. Since they aren't
loaded at boot time, I assume the *bdwlan.elf* code loads at least one
of these blobs. It may load all of them, but because they are all the
same size, I think like the *bdwlan.b[0-9][0-9]* files, these are each
device specific model. Disassembling bdwlan.elf, is an AARCH32 ELF
file using the AARCH32 Thumb (T32) instruction set.

## Wireless Processor SubSystem (WPSS)

This is the firmware that used for WiFi & Bluetooth support. It
includes the baseband digital signal processing, an RF transceiver, and
power amplifier. It contains an ARM Cortex-M3 or M4 core for
application code. It looks like it also contains a RISCV core. The
blob that seems to be an Intel x86_32 is suspicious.

* wpss.b00 - ELF 32-bit LSB executable, QUALCOMM DSP6
* wpss.b01 - ATMel AVR 8 Cortex-M little endian
* wpss.b02 - ELF64, little endian AARCH64 binary
* wpss.b03 - ELF64, little endian AARCH64 binary
* wpss.b04 - ELF64, little endian AARCH64 binary
* wpss.b05 - ELF6 4 little endian relocatable, AARCH64
* wpss.b06 - looks like boot code and contains multiple files
* wpss.b07 - ELF32 little endian RISCV32 binary
* wpss.b08 - ELF32 little endian Intel i386 binary
* wpss.b09 - 64 bit little AARCH64 binary

## The Software Stack

There are several layers of software used to interface with the
firmware. All of the source code for these layers are part of the
Qualcomm open source release. The architecture of the wireless software
stack is explained in detail [in this
document](https://deepwiki.com/TechNexion/qcacld-2.0/1-overview), so
this is just a quick summary.

### [Host Device Driver (HDD)](https://deepwiki.com/TechNexion/qcacld-2.0/2-host-device-driver-(hdd)#host-device-driver-hdd)

This is the primary interface between the kernel's networking stack
and the driver.

### [Station Management Entity (SME)](https://deepwiki.com/TechNexion/qcacld-2.0/1.1-system-architecture#station-management-entity-sme)

This is the interface between the HDD and the protocol engine.

## [Wireless Module Interface (WMI)](https://deepwiki.com/TechNexion/qcacld-2.0/5.1-wireless-module-interface-(wmi)#wmi-architecture)

This is command and event protocol used between the driver and the firmware.

### [Wireless Management Agent (WMA)](https://deepwiki.com/TechNexion/qcacld-2.0/5-wireless-management-agent-(wma)#wireless-management-agent-wma)

This is the interface between the SME and the WMI.

## [Hardware Interface (HIF)](https://deepwiki.com/TechNexion/qcacld-2.0/1-overview#hardware-interface-hif)

This interfaces with the actual hardware.


