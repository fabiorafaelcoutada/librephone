# Wifi & Bluetooth Support

The [Qualcomm
wcn6750](https://www.qualcomm.com/wi-fi/products/fastconnect/fastconnect-6700)
chipset is used for wifi support when coupled with a SnapDragon
SoC. Since datasheets and most all documentation requires an NDA with
Qualcomm, about the only decent doc is the Linux [kernel
patch](https://lwn.net/Articles/889433/) that adds wcn6750
support. This uses the atk11k device driver, which supports several
other chipsets. The architecture of the wireless software stack is
explained [in this
document](https://deepwiki.com/TechNexion/qcacld-2.0/1-overview).

This chip appears to have an embedded ARM core, and possibly a RISCV
core as well. These blobs are in the *modem.img* file, and are in the
*modem/image/qca6750* directory. On a device, they're in the
*/vendor/firmware_mnt/image/qca6750/* directory.

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

## QCA6750 Blobs

The higher level blobs use the WPSS to control the hardware. There are
three types of blobs. There are many files with the pattern
*bdwlan.b[0-9][0-9]* which are Board Device Files (BDF) used to
customize the software for a particular chipset. Only one is used, so
the rest can be ignored. The active file gets compiled into a
*bdwlan.bin* file. The only file loaded at boot time is *bdwlan.elf*,
which is a 32 bit Armv7 file.

In addition, there are also many files with the pattern
*bdwlan.e[0-9][0-9]*, which are 32bit AARCH32 files. Since they aren't
loaded at boot time, I assume the bdwlan.elf code loads at least one
of these blobs. It may load all of them, but because they are all the
same size, I think like the __bdwlan.b*__ files, these are each device
specific.
