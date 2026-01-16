# The ath11k Driver

This is the device driver that works with the Qualcomm WCN6750 that
provides support for the non cellular radio traffice. There are
multiple layers of APIs and data protocols used to support the radio
devices. The ath11k driver code is copyrighted by both Qualcomm and
the Linux Foundation and uses a [BSD-3-Clause-Clear
license](https://spdx.org/licenses/BSD-3-Clause-Clear.html). This is
the same driver source as used by the Linux kernel as well. The layers
in order are:

* Android kernel
* WMA - Wireless Management Agent (WMA)
* WMI - Wireless Module Interface
* HTC - Host-Target Communication
* HIF - Host interconnect Framework
* PCI - PCIe
* CE - Copy Engine

## Qualcomm Open Source Release

Qualcomm has released code for the WCN6750 that handles the higher
level protocols, *Wireless Module Interface (WMI)* and *Wireless
Management Agent (WMA)*, and the *Host Device Driver (HDD)*. The
kernel module's source code for that can be [found
here](https://github.com/ArianK16a/android_kernel_fairphone_sm7635-modules/tree/lineage-23.2/qcom/opensource/wlan). It
is copyrighted by both Qualcomm and the Linux Foundation and uses a
[ISC license](https://spdx.org/licenses/ISC.html).

### Host Device Driver (HDD)

This is the interface between the lower level code in the WMA and the
kernel device driver, with the source code in the
*qcacld-3.0/core/hdd* directory. This is a higher level interface than
anything this project needs to look into in any detail.

### Wireless Management Agent (WMA)

This is the interface for higher level commands from the HDD for the
WMI, with the source code in the *qcacld-3.0/core/wma*
directory. This is a higher level interface than anything this project
needs to look into in any detail.

### Wireless Module Interface (WMI)

This is primary interface between the driver and the blob. This is an
bi-directional asynchronus command layer for controlling the radio
device. The source for this is in two directories
*qcacld-3.0/components/wmi* and *qca-wifi-host-cmn/wmi*. There is also 
a file in the ath11k driver directory, *ath11k/wmi.c* and
*ath11k/wmi.h* that uses the qca library. This defines the
commands used in the data stream between the kernel and the hardware.

This is a good layer to document the API, and get some insight into what a
reimplemented blob would need to support. This uses the HTC for the
transport layer to the blob.

### Host-Target Communication (HTC)

This sends or recieves the commands from the WMI. This doesn't
directly talk to the blob, it uses the HIF for the actual data
exchange. The source code for this is in two directories. The primary
one is in the qca library from Qualcomm, *qca-wifi-host-cmn/htc*, and
the ath11k driver has an *htc.c* file that uses this library.

### Host interconnect Framework (HIF)

Abstracts the access to different bus types. Currently only supports
PCI, but it’s easy to add different bus types. The source code for
this is in two directories. The primary one is in the qca library from
Qualcomm, *qca-wifi-host-cmn/hif*. The ath11k driver has a file
*ath11k/hif.h* that connects the library to the driver.

### PCIe Interface

This is the lowest level API for communicating with the hardware. The
primary source code in in the qca library in the
*qca-wifi-host-cmn/hif/src/ipcie* and *qca-wifi-host-cmn/hif/src/pcie*
directories. The ath11k driver has a file *ath11k/pci.c* that connects
the library to the driver.

#### The Copy Engine

Communication with the blob is done using the Copy Engine, which is a
bi-directional ring of DMA buffers. The source file that defines the
data structures is in the *ath/ath11k/core.h* file. The 3 data
structures of interest are These are *ath11k_ce*, *ath11k_ce_pipe*,
*ath11k_ce_ring*.
