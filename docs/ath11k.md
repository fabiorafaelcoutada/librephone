# The ath11k Driver

This is the device driver that works with the Qualcomm WCN6750 that
provides support for the non cellular radio traffice. There are
multiple layers of APIs and data protocols used to support the radio
devices. The ath11k driver code is copyrighted by both Qualcomm and
the Linux Foundation and uses a [BSD-3-Clause-Clear
license](https://spdx.org/licenses/BSD-3-Clause-Clear.html). This is
the same driver source as used by the Linux kernel as well. The layers
in order are:

* HDD  - Host Device Driver
* WMA  - Wireless Management Agent (WMA)
* WMI  - Wireless Module Interface  (control plane)
* HTT  - Host-to-Target Transport   (data plane)
* HTC  - Host-Target Communication  (transport layer for WMI and HTT)
* HIF  - Host Interconnect Framework
* SNOC/AHB - Physical bus for WCN6750 (or PCIe for QCA6390/other chips)
* CE   - Copy Engine (DMA engine)

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

Both WMI (control plane) and HTT (data plane) run over HTC as a
shared transport.

### Host-to-Target Transport (HTT)

HTT is the **data-plane protocol** between the driver and the blob,
operating in parallel to WMI (which handles the control plane). HTT
carries all data frames and operational events — it is the protocol
the blob **must** implement for the radio to function.

The HTT protocol is defined in `fw-api/fw/htt.h` (~19,000 lines in the
Qualcomm firmware headers). This is the contractual specification of
the driver‒blob interface. Full protocol details and the initialization
handshake are documented in `htt.md`.

On the Linux kernel side, HTT is implemented in:
- `ath/ath11k/htt.c` — host-side HTT logic
- `ath/ath11k/htt.h` — HTT data structures
- `ath/ath11k/htc.c`  — HTC transport layer (used by both HTT and WMI)

The initialization sequence (`htt_attach_target()`) sends three
mandatory messages after the HTC connection is established:

1. **VERSION_REQ** → blob replies **VERSION_CONF** (capability negotiation)
2. **FRAG_DESC_BANK_CFG** → configures the TX fragment DMA region
3. **RX_RING_CFG** → configures the RX DMA ring base address and size

Without these, the blob will not respond and the radio cannot be used.

### Host Interconnect Framework (HIF)

Abstracts the access to different bus types. For the WCN6750
(integrated into the SM7635 SoC) the transport is **SNOC/AHB**
(System Network-on-Chip / Advanced High-performance Bus). PCIe is used
for discrete chips such as the QCA6390. The source code for this is in
two directories. The primary one is in the qca library from Qualcomm,
*qca-wifi-host-cmn/hif*. The ath11k driver has a file *ath11k/hif.h*
that connects the library to the driver.

On Android, the WPSS firmware presents a **fake PCI device** to the
rest of the stack because the real PCI bus cannot be probed on an
integrated SoC with no physical PCIe signaling. The HIF/SNOC layer
bridges this abstraction. See the `hif.md` document for a detailed
architectural description.

### Physical Bus — SNOC/AHB (WCN6750) / PCIe (other chips)

For the WCN6750, the physical bus is **SNOC/AHB**, a memory-mapped
on-chip interconnect. The source code for the SNOC transport is in
*qca-wifi-host-cmn/hif/src/snoc/*, identified by
`#define HIF_TYPE_QCA6750 23` in `hif.h`. There is no physical PCIe
bus on the WCN6750.

For discrete chips (QCA6390, etc.) the transport is standard PCIe, with
source code in *qca-wifi-host-cmn/hif/src/ipcie* and
*qca-wifi-host-cmn/hif/src/pcie*, plus the ath11k driver file
*ath11k/pci.c*.

**Fake PCI note:** The WPSS firmware presents a fake PCI device to the
driver because the integrated chip cannot probe the real PCI bus.
WPSS abstracts this using AHB while exposing a PCI device interface to
the upper layers of the stack. The HIF/SNOC layer is the bridge
between these abstractions.

#### The Copy Engine

Communication with the blob is done using the Copy Engine, which is a
bi-directional ring of DMA buffers. The source file that defines the
data structures is in the *ath/ath11k/core.h* file. The 3 data
structures of interest are *ath11k_ce*, *ath11k_ce_pipe*,
*ath11k_ce_ring*.

**Important clarification:** The Copy Engine is simply a **programmable
DMA controller** that allocates SoC memory for the firmware. It does
not implement its own protocol logic beyond moving data between the
host and the blob. A free-software blob **would not need to
reimplement CE** — it only needs to respond to the HTT and WMI
protocols that run *over* CE.

Furthermore, most WPSS blob files are **data files** (calibration
tables, RF configuration, certificates), not executables. The actual
executable code is a minority of the total image, which significantly
reduces the scope of a hypothetical free blob.

### Testing / Diagnostic API (TLV files)

There is a low-level testing and diagnostic API for the WCN6750,
separate from the production HTT/WMI stack. The relevant headers are
located in:

- `fw-api/hw/qca6750/` — chip-specific TLV tag definitions (418 tag
  types across 40+ categories)
- `qca-wifi-host-cmn/wmi/` — TLV support at the WMI layer

Code comments describe this API as supporting **"external testing"**.
This appears to be a separate debugging/factory-test interface.

**Caveat:** As noted by Rob Savoye (email 2026-06-21), this assessment
is based on educated reverse engineering of the header files; the
actual runtime structure may differ. See `fw-api/hw/qca6750/v1/` for
the raw TLV tag definitions.

### Reference Sources

The primary specification for the driver‒blob protocol is the
Qualcomm firmware API headers in **`fw-api/fw/`**, most notably:

- `fw-api/fw/htt.h` (~19,000 lines) — HTT protocol definition
- `fw-api/fw/wmi.h` — WMI protocol definition
- `fw-api/hw/qca6750/` — chip-specific headers (TLV tags, CE config)

These headers represent the contractual interface between the driver
and the blob, and should be treated as the authoritative source for
any free-software reimplementation effort.

SPDX-License-Identifier: AGPL-3.0-or-later
