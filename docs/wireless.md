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

This chip appears to have an embedded 8 bit ATMel AVR core, and
possibly a RISCV32 core as well. These blobs are in the *modem.img*
file, and are in the
[modem/image/qca6750](https://librephone.fsf.org/blobs/FP6/modem/image/qca6750/)
directory. On a device, they're in the
*/vendor/firmware_mnt/image/qca6750/* directory.

## Tools

A variety of open source tools have been used to attempt to identify
all the files. Most of the fancy GUI based reverse engineering tools
use the the [GNU Binutils](https://www.gnu.org/software/binutils/) in
the backend. This includes *nm* for listing symbols (if any exist) and
*objdump* which can disassemble the ELF files into assembly code. One
thing I have noticed is the Binutils is the only one that can
disassemble the AARCH32 T32 (Thumb) instruction set, which is a subset
of the AARCH32 A32 instruction set. It's executables are encoded
differently for a small executable which is an important
difference. For objdump add *--disassembler-options=force-thumb*( to
the command line to get clean output. The
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
which is a 32 bit AARCH32 Thumb file. The format of the BDF files is
unknown as the only documentation available from Qualcomm requires an
NDA.

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
device specific model. bdwlan.elf, is an AARCH32 ELF file using the
AARCH32 Thumb (T32) instruction set.

## Wireless Processor SubSystem (WPSS)

These are the blobs used for WiFi & Bluetooth support. It includes the
baseband digital signal processing, an RF transceiver, and power
amplifier. It seems to contain an ATmel AVR core for some
application code. It looks like it also contains a RISCV core. The
blob that seems to be an Intel x86_32 is suspicious.

The 3 blobs, wpss.b02, wpss.b03, and wpss.b04 are a bit
mysterious. All the tools have had issues identifying them, but
they do seem to agree they are for the AARCH architecture. This is
probably because the AARCH architecture supports multiple instructions
sets, and the AARCH32 core can execute both A32 and T32 instructions,
so in a binary these are often mixed in the same binary file. These
are not ELF executables, these are raw binary files that have to be
loaded at a specific address.

Dissasembling them gives varying results, but looking through the code
it appears to  be a 16 bit AARCH32 Thumb-2. Reading dissasembled code
can be misleading, as often it looks good, but you have to really dig
into what the ASM code appears to be doing to be sure. I also look for
instructions that look weird, and double check the ARM assembly
manuals just to make sure it is legit.

* wpss.b00 - ELF 32-bit LSB executable, QUALCOMM DSP6
* wpss.b01 - ATMel AVR 8 bit little endian
* wpss.b02 - 16/32 bit Thumb-2 little endian AARCH32 binary ??
* wpss.b03 - 16/32 bit Thumb-2 little endian AARCH32 binary
* wpss.b04 - 16/32 bit Thumb-2 little endian AARCH32 binary ??
* wpss.b05 - ELF64 little endian relocatable, AARCH64
* wpss.b06 - Multiple AARCH32 data files
* wpss.b07 - ELF32 little endian RISCV32 binary ?
* wpss.b08 - ELF32 little endian Intel i386 binary
* wpss.b09 - data ?
* wpss.b10 - data file
* wpss.b12 - 3 certificates in DER format (x509 v3)
* wpss.mdt - ELF 32-bit LSB executable, QUALCOMM DSP6

The wcn6750 uses the platform device (AHB) in the kernel because it
can't be probed at boot time. I'm assuming that's what wpss.b05 does.
Once probed and booted communication switches to working like a PCIe
device.

## Device Tree

The memory address for communication between the driver and the
firmware is in the kernel device tree file. In the kernel there are
several files that get included by other device tree files. Since the
wcn6750 is a PCI device, in the device tree file it sets the
__msi_addr__, which is then used elsewhere in the kernel. For the
FP6, this is *0x17110040*. There is also an IOVA IPA address which is
*0xc0000000*, which is what is used by the PCI driver and the wcn6750
blobs.

IOMMU creates a direct access I/O connection to physical memory
instead of a DMA connection.

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


