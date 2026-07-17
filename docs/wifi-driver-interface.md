# WiFi Driver ↔ Blob Interface — WCN6750 (QCA6750 "Moselle")

SPDX-License-Identifier: CC-BY-SA-4.0
SPDX-FileCopyrightText: 2026 Gustavo Paredes <lu2jgp@gmail.com>

## Abstract

This document describes the **complete interface contract** between the
Qualcomm open-source WLAN host driver (qcacld-3.0 / ath11k) and the
proprietary **WPSS** (WiFi Processor SubSystem) firmware blob that runs
on the WCN6750 radio chip integrated in the SM7635 SoC (Fairphone 6).

The goal is to define every protocol layer, message structure, and
initialization handshake the blob must support — information needed to
design a **Free Software replacement** for the WPSS firmware.

## 1. Stack Overview

The WiFi stack on the WCN6750 spans six protocol layers, each described
in detail in the sections below:

```
┌──────────────────────────────────────────────────────────┐
│                     Linux Kernel                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │  HDD — Host Device Driver (wlan_hdd_*)               ││
│  │  WMA — Wireless Management Agent                     ││
│  ├────────────────┬─────────────────────────────────────┤│
│  │   WMI          │          HTT                        ││
│  │  (Control)     │         (Data)                      ││
│  ├────────────────┴─────────────────────────────────────┤│
│  │  HTC — Host-Target Communication (transport mux)     ││
│  ├──────────────────────────────────────────────────────┤│
│  │  HIF — Host Interconnect Framework (bus abstraction) ││
│  │  ┌───────────────────┬──────────────────────────────┐││
│  │  │  SNOC (WCN6750)   │  PCIe (QCA6390, other chips) │││
│  │  └───────────────────┴──────────────────────────────┘││
│  ├──────────────────────────────────────────────────────┤│
│  │  CE — Copy Engine (DMA ring management)              ││
│  └──────────────────────────────────────────────────────┘│
│                          │                               │
│                    ┌─────┴─────┐                         │
│                    │  SNOC bus │ (AHB-based SoC fabric)  │
│                    └─────┬─────┘                         │
│                          │                               │
│ ═════════════════════════╪══════════════════════════════ │
│                          │        TRUSTZONE / SCM        │
│  ┌───────────────────────┴──────────────────────────────┐│
│  │  WPSS firmware blob ( Qualcomm® proprietary )        ││
│  │  — loaded by PIL (Peripheral Image Loader)           ││
│  │  — authenticated by TrustZone via SCM calls          ││
│  │  — runs on Hexagon DSP core inside WCN6750           ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### Source Code Locations

| Component | Path in `sm7635-modules/` |
|-----------|---------------------------|
| Firmware API headers (HTT, WMI, HTC) | `qcom/opensource/wlan/fw-api/fw/` |
| Host driver core | `qcom/opensource/wlan/qcacld-3.0/core/` |
| WMI client library | `qcom/opensource/wlan/qca-wifi-host-cmn/wmi/` |
| HTC transport | `qcom/opensource/wlan/qca-wifi-host-cmn/htc/` |
| HIF / CE infrastructure | `qcom/opensource/wlan/qca-wifi-host-cmn/hif/` |
| FTM test mode | `qcom/opensource/wlan/qca-wifi-host-cmn/ftm/` |

> All source is released under ISC license (Qualcomm) or BSD-3-Clause-Clear (Linux Foundation).
> Repository: [ArianK16a/android_kernel_fairphone_sm7635-modules](https://github.com/ArianK16a/android_kernel_fairphone_sm7635-modules) (branch `lineage-23.2`).

---

## 2. Physical Transport: SNOC + Copy Engine

### 2.1 SNOC — "Fake PCI" over AHB

The WCN6750 is an **integrated** WiFi chip (die-stacked or on-SoC), not a
discrete PCIe card. The transport is **SNOC** (System Network-on-Chip), an
AHB-based interconnect built into the Qualcomm SM7635 SoC fabric.

The WPSS firmware presents a *platform device* — not a PCI device. No PCI
enumeration occurs. Yet the driver uses PCI-like abstractions:

- **MMIO BAR** — WPSS provides a base address for memory-mapped I/O registers
- **VID:PID** `0x17cb:0x1105` — hardcoded `pci_device_id` for driver matching
- **CE registers** — Copy Engine control registers mapped into MMIO space

**Source**: `hif/src/snoc/if_snoc.c`, `hif/src/dispatcher/multibus.c`

```c
/* multibus.c: bus type dispatcher */
if (bus_type == QDF_BUS_TYPE_SNOC) {
    hif_initialize_snoc_ops(&bus_ops);  // assign SNOC vtable
}
```

### 2.2 Copy Engine — DMA Pipes

The CE (Copy Engine) is a hardware-assisted DMA engine that moves data
between host memory and WPSS memory. Each CE provides a **bidirectional
ring buffer** with source and destination descriptor rings.

**CE Pipe assignments for WCN6750** (from `hif/src/ce/ce_assignment.h`):

| Pipe | Direction | Protocol | Purpose |
|------|-----------|----------|---------|
| CE0  | Host → Target | HTC control | HTC setup + raw streams |
| CE1  | Target → Host | HTT + HTC | HTT T2H messages + HTC control responses |
| CE2  | Target → Host | WMI | WMI events from blob to host |
| CE3  | Host → Target | WMI | WMI commands from host to blob |
| CE4  | Host → Target | HTT | HTT H2T messages (data-path, TX frames) |
| CE5  | Host → Target | IPA/HTC | IPA µController (optional offload) |
| CE6  | reserved | memcpy | Target autonomous HIF memcpy |
| CE7  | Target → Host | PKTLOG | Packet log for debugging |
| CE8  | Target → Host | HTT | Secondary HTT (dual-band / multi-core) |

Each CE pipe has a configuration specifying:
- Number of source descriptors
- Number of destination descriptors
- Buffer sizes (typical: 2048 bytes for control, 256 bytes for TX)
- IRQ flags (enable/disable interrupts per-pipe)

---

## 3. HIF — Host Interconnect Framework

HIF abstracts the bus type (SNOC, PCIe, AHB) behind a uniform API.
All upper layers call `hif_read_write()`, `hif_map_service()`, `hif_enable()`
through an opaque `hif_handle_t`.

### 3.1 Bus Operations VTable

`struct hif_bus_ops` (defined in `hif/src/dispatcher/multibus.h`) contains
~40 function pointers implementing the bus-specific primitives:

```c
struct hif_bus_ops {
    int (*bus_open)(void **hif_ctx, ...);
    void (*bus_close)(void *hif_ctx);
    int (*bus_configure)(...);
    int (*bus_suspend)(...);
    int (*bus_resume)(...);
    void (*bus_enable_bus)(...);
    void (*bus_disable_bus)(...);
    int (*ce_send)(...);        // DMA transfer to blob
    int (*ce_recv)(...);        // DMA transfer from blob
    // ... ~30 more
};
```

For WCN6750, `hif_initialize_snoc_ops()` (`multibus_snoc.c`) assigns the SNOC
implementations of these functions.

### 3.2 Interrupt Handling

On SNOC, the interrupt handler is `hif_snoc_interrupt_handler()` in
`hif/src/ce/ce_tasklet.c`. It dispatches to per-CE tasklets:

- **CE1** → HTT T2H + HTC RX tasklet
- **CE2** → WMI RX tasklet
- **CE7** → PKTLOG tasklet

Each tasklet reads its CE ring, pulls DMA descriptors, and passes the
data buffer to the upper protocol layer.

### 3.3 MMIO Access

All CE register access goes through MMIO helpers in `hif/src/hif_io32.h`:

```c
static inline A_UINT32 hif_read32_mb(A_UINT32 *address) {
    return *(volatile A_UINT32 *)address;
}
static inline void hif_write32_mb(A_UINT32 *address, A_UINT32 value) {
    *(volatile A_UINT32 *)address = value;
}
```

The WPSS blob provides the MMIO BAR base address during platform device
probing (see §7 PIL boot).

---

## 4. HTC — Host-Target Communication

HTC is a lightweight transport **multiplexing** layer. Both WMI (control plane)
and HTT (data plane) travel over HTC. It provides:

- **Endpoints** — logical connections multiplexed onto CE physical pipes
- **Credit-based flow control** — prevents the blob's buffer from overflowing
- **Service IDs** — each endpoint carries a specific upper-layer protocol

### 4.1 HTC Frame Format

```c
// fw-api/fw/htc.h
typedef PREPACK struct _HTC_FRAME_HDR {
    A_UINT32  EndpointID : 8,   // 0 = control, 1-7 = data endpoints
              Flags      : 8,   // CRC, sequence, bundle flags
              PayloadLen : 16;  // payload byte count
    A_UINT32  ControlBytes0 : 8,
              ControlBytes1 : 8,
              reserved : 16;
} POSTPACK HTC_FRAME_HDR;
```

Header is 8 bytes. Max payload: 4088 bytes. Total max frame: 4096 bytes.

### 4.2 HTC Service IDs

Each service is identified by a 16-bit ID: `(group << 8) | index`.

| Service ID | CE Pipe | Direction | Protocol |
|------------|---------|-----------|----------|
| `WMI_CONTROL_SVC` (0x0100) | CE3 (out) / CE2 (in) | Bidir | WMI commands & events |
| `WMI_DATA_BE_SVC` (0x0101) | CE3/CE2 | Bidir | WMI Best Effort data |
| `WMI_DATA_BK_SVC` (0x0102) | CE3/CE2 | Bidir | WMI Background data |
| `WMI_DATA_VI_SVC` (0x0103) | CE3/CE2 | Bidir | WMI Video data |
| `WMI_DATA_VO_SVC` (0x0104) | CE3/CE2 | Bidir | WMI Voice data |
| `HTT_DATA_MSG_SVC` (0x0300) | CE4 (out) / CE1 (in) | Bidir | HTT messages |
| `HTT_DATA2_MSG_SVC` (0x0301) | CE8 (in) | In | Parallel RX channel |

### 4.3 HTC Initialization Sequence

```
Host (driver)                         Target (blob / WPSS)
──────────────────────────────────────────────────────────
  HTC_MSG_READY (credits available)
                                 ←    HTC_READY_MSG (target credits + max endpoints)

  HTC_MSG_CONNECT_SERVICE_ID      →
    (WMI_CONTROL_SVC, HTT_DATA_MSG_SVC)
                                 ←    HTC_MSG_CONNECT_SERVICE_RESPONSE_ID
                                       (accepted/rejected, endpoint ID assigned)

  HTC_MSG_SETUP_COMPLETE_ID       →    (all services connected)
                                 ←    HTC_MSG_SETUP_COMPLETE_EX_ID
──────────────────────────────────────────────────────────
  HTC endpoints operational
```

The blob must advertise:
- **Credit count** — how many receive buffers the blob has available
- **Credit size** — max bytes per credit unit
- **Max endpoints** — how many logical connections the blob supports (min 4)

---

## 5. WMI — Control Path

WMI (Wireless Module Interface) is the **control-plane protocol**. Every
high-level WiFi operation — scanning, connecting, setting channels, managing
keys — maps to a WMI command/event pair.

> **Key distinction**: WMI travels over CE2 (T→H) and CE3 (H→T).
> HTT (see §6) travels over CE1 (T→H) and CE4 (H→T).
> They share HTC as transport but are different CE pipes.

### 5.1 WMI Message Header

```c
// fw-api/fw/wmi.h
typedef PREPACK struct {
    A_UINT32  commandId : 24,  // WMI command/event ID
              reserved  : 2,   // WMI endpoint ID
              plt_priv  : 6;   // platform private
} POSTPACK WMI_CMD_HDR;
```

The `commandId` field is a 24-bit value following the Qualcomm TLV scheme:
`WMI_CMD_GRP_START_ID(grp_id) = (grp_id << 12) | 0x1`

### 5.2 WMI Initialization Sequence

The first step after HTC setup: the blob must announce its capabilities
to the host via two WMI events.

```
Host (driver)                         Target (blob)
──────────────────────────────────────────────────────────
                                    ← WMI_SERVICE_READY_EVENTID (0x1)
                                      - firmware version
                                      - WMI protocol version
                                      - list of supported service IDs (bitmap)
                                      - target type (QCA6750 = 28)
                                      - memory regions, max peers, max VDEVs

                                    ← WMI_READY_EVENTID (0x2)
                                      - firmware build info
                                      - PHY capabilities

  WMI_INIT_CMDID (0x1)              →  Complete host capability negotiation
──────────────────────────────────────────────────────────
  WMI control path operational
```

The **service bitmap** is critical: the blob announces which WMI commands
it supports. The host queries this bitmap before sending any command
outside the mandatory set.

### 5.3 Key WMI Commands (Host → Blob)

| Command | CmdID | Group | Purpose |
|---------|-------|-------|---------|
| `WMI_INIT_CMDID` | `0x1` | — | Finalize host-side init |
| `WMI_START_SCAN_CMDID` | `0x3001` | Scan | Initiate WiFi scan |
| `WMI_STOP_SCAN_CMDID` | `0x3002` | Scan | Abort scan |
| `WMI_VDEV_CREATE_CMDID` | `0x5001` | VDEV | Create virtual interface |
| `WMI_VDEV_DELETE_CMDID` | `0x5002` | VDEV | Destroy virtual interface |
| `WMI_VDEV_UP_CMDID` | `0x5003` | VDEV | Bring vdev up |
| `WMI_VDEV_STOP_CMDID` | `0x5004` | VDEV | Stop vdev |
| `WMI_VDEV_DOWN_CMDID` | `0x5005` | VDEV | Bring vdev down |
| `WMI_PEER_CREATE_CMDID` | `0x6001` | Peer | Create peer (STA/AP association) |
| `WMI_PEER_DELETE_CMDID` | `0x6002` | Peer | Remove peer |
| `WMI_PDEV_UTF_CMDID` | `0x1d002` | Misc | FTM/UTF test mode command |
| `WMI_ECHO_CMDID` | `0x1d001` | Misc | Ping blob (health check) |

### 5.4 Key WMI Events (Blob → Host)

| Event | EvtID | Purpose |
|-------|-------|---------|
| `WMI_SERVICE_READY_EVENTID` | `0x1` | Firmware capability announcement (mandatory) |
| `WMI_READY_EVENTID` | `0x2` | Firmware ready confirmation |
| `WMI_PDEV_UTF_EVENTID` | `0x1d002` | FTM/UTF test mode response |
| `WMI_ECHO_EVENTID` | `0x1d001` | Echo reply (health) |

### 5.5 WMI Endpoint Assignment

WMI uses multiple HTC endpoints for traffic prioritization:

| WMI EP | QoS | Use |
|--------|-----|-----|
| `WMI_EP_APSS` (0x0) | Control | All WMI commands/events from app processor |
| `WMI_EP_LPASS` (0x1) | Control | Low-power audio DSP commands |
| `WMI_EP_MODEM` (0x4) | Control | Modem processor commands |

---

## 6. HTT — Data Path

HTT (Host-to-Target Transport) is the **data-plane protocol**. It carries all
WiFi data frames, TX completions, RX indications, and operational events.

> Full protocol details with initialization handshake, FRAG_DESC_BANK_CFG,
> and RX_RING_CFG are documented in `htt.md`.

### 6.1 Message Summary

HTT 3.148 defines:
- **44 H2T message types** (Host → Target, `enum htt_h2t_msg_type`)
- **64 T2H message types** (Target → Host, `enum htt_t2h_msg_type`)

#### H2T Messages — Critical Subset

| # | Type | Value | Required | Purpose |
|---|------|-------|----------|---------|
| 1 | `VERSION_REQ` | `0x0` | ✅ | HTT version negotiation |
| 2 | `TX_FRM` | `0x1` | ✅ | Transmit WiFi data frame |
| 3 | `RX_RING_CFG` | `0x2` | ✅ | Configure RX DMA ring |
| 4 | `STATS_REQ` | `0x3` | 🔶 | Request statistics |
| 5 | `SYNC` | `0x4` | 🔶 | Synchronization barrier |
| 6 | `AGGR_CFG` | `0x5` | 🔶 | Configure frame aggregation |
| 7 | `FRAG_DESC_BANK_CFG` | `0x6` | ✅ | TX fragment descriptor bank |
| 9 | `WDI_IPA_CFG` | `0x8` | 🔹 | IPA offload configuration |
| 11 | `SRING_SETUP` | `0xb` | 🔹 | Shared ring setup (Lithium targets) |
| 12 | `RX_RING_SELECTION_CFG` | `0xc` | 🔹 | Flow steering / RX ring selection |
| 17 | `PPDU_STATS_CFG` | `0x11` | 🔹 | PPDU statistics configuration |
| 33 | `MSI_SETUP` | `0x1f` | 🔹 | MSI interrupt setup |

✅ = mandatory for any re-implemented blob
🔶 = needed for normal operation
🔹 = optional / advanced features

#### T2H Messages — Critical Subset

| # | Type | Value | Required | Purpose |
|---|------|-------|----------|---------|
| 1 | `VERSION_CONF` | `0x0` | ✅ | Version negotiation reply |
| 2 | `RX_IND` | `0x1` | ✅ | Received data frame indication |
| 3 | `RX_FLUSH` | `0x2` | 🔶 | Flush RX buffer |
| 4 | `PEER_MAP` | `0x3` | ✅ | Map peer ID to MAC address |
| 5 | `PEER_UNMAP` | `0x4` | 🔶 | Unmap peer |
| 6 | `RX_ADDBA` | `0x5` | 🔶 | Block ACK add request |
| 7 | `RX_DELBA` | `0x6` | 🔶 | Block ACK delete |
| 8 | `TX_COMPL_IND` | `0x7` | ✅ | TX completion indication |
| 10 | `STATS_CONF` | `0x9` | 🔶 | Statistics response |
| 11 | `RX_FRAG_IND` | `0xa` | 🔶 | Fragmented RX indication |
| 17 | `RX_PN_IND` | `0x10` | 🔶 | Packet number (security) |
| 18 | `RX_OFFLOAD_DELIVER_IND` | `0x11` | 🔹 | RX offload delivery |
| 19 | `RX_IN_ORD_PADDR_IND` | `0x12` | 🔶 | RX indication with physical address |
| 31 | `PEER_MAP_V2` | `0x1e` | 🔶 | Peer map (extended) |
| 34 | `FLOW_POOL_RESIZE` | `0x21` | 🔹 | Flow pool management |

### 6.2 Memory Architecture

The blob must manage these shared-host-memory structures:

1. **RX Ring** — circular buffer where the blob DMAs received packets.
   Configured via `HTT_H2T_MSG_TYPE_RX_RING_CFG`:
   - Base physical address
   - Number of entries (typically 1024–4096)
   - Entry size (typically 2048 bytes)
   - Shadow register for RX head pointer

2. **Fragment Descriptor Bank** — pre-allocated DMA region where the blob
   reads TX MSDU fragment descriptors. Configured via
   `HTT_H2T_MSG_TYPE_FRAG_DESC_BANK_CFG`.

3. **MSDU Extension Descriptor** — optional per-frame descriptor with
   detailed TX specifications (rate control, aggregation hints, cookies).

---

## 7. Boot / PIL Sequence

Before any WiFi protocol messages can be exchanged, the WPSS firmware
must be loaded into the WCN6750's Hexagon DSP and authenticated.

### 7.1 PIL (Peripheral Image Loader)

The Qualcomm PIL subsystem loads firmware images into remote processors:

```
1. Linux kernel (subsystem_restart_dev)
   │
2. PIL driver: qcom_pil_load()
   │  - Load wpss.mbn (or wpss.b00-wpss.b12) from /vendor/firmware_mnt/image/
   │  - Parse ELF headers, map segments into DSP memory
   │  - Set up carve-out memory regions (CMA)
   │
3. SCM (Secure Channel Manager) / TrustZone
   │  - scm_call(TZ_PIL_AUTH_QDSP6, ...) — verify firmware signature
   │  - Reset Hexagon DSP
   │  - Release DSP from reset — firmware begins executing
   │
4. Firmware init
   │  - WPSS firmware initializes internal state
   │  - Configures CE registers in MMIO space
   │  - Asserts WLAN_EN GPIO to power on radio hardware
   │  - Begins responding on HTC endpoint 0 (control)
   │
5. Driver probes
   │  - PLD (Platform Driver) layer detects WPSS device
   │  - HIF bus open → HTC connect → WMI service ready → HTT attach
```

The SCM call IDs for WPSS PIL auth on SM7635 (from `docs/wpss.b12.md`):

| SCM Call | ID | Purpose |
|----------|----|---------|
| `PAS_AUTH_AND_RESET` | `0x4` | Authenticate and start WPSS DSP |
| `PAS_SHUTDOWN` | `0x5` | Gracefully shut down WPSS |
| `PAS_IS_SUPPORTED` | `0x9` | Check if WPSS PIL is available |

### 7.2 Firmware Image Format

The WPSS firmware is distributed as:

| Format | File(s) | Purpose |
|--------|---------|---------|
| **MBF** (single file) | `wpss.mbn` | PostmarketOS: single hashed+authenticated firmware |
| **Split** (12 segments) | `wpss.b00`–`wpss.b12` | LineageOS: 12-chain certificate chain + ELF segments |

Both formats are ELF files with X.509 certificate chains embedded. The
PIL/TrustZone validates the certificate chain before allowing DSP execution.

> Certificate chain analysis: see `docs/wpss.b12.md`

---

## 8. FTM / UTF — Test Mode Interface

The Factory Test Mode (FTM), also known as Unified Test Framework (UTF), is
a **raw command/response channel** between the host and the WPSS blob. It is
used for RF calibration, production testing, and hardware diagnostics.

> Full details: see `docs/ftm.md`

FTM commands travel over **WMI** (not HTT), using the Misc group:

- Command: `WMI_PDEV_UTF_CMDID` (`0x1d002`) — host → blob
- Event: `WMI_PDEV_UTF_EVENTID` (`0x1d002`) — blob → host

FTM is only active when the driver is loaded with `device_mode == QDF_GLOBAL_FTM_MODE`.

### 8.1 Entry Points

- **ioctl**: `FTM_IOCTL_UNIFIED_UTF_CMD` (0x1000) / `FTM_IOCTL_UNIFIED_UTF_RSP` (0x1001)
- **nl80211 testmode**: `WLAN_CFG80211_FTM_CMD_WLAN_FTM = 0`

### 8.2 Data Flow

```
Userspace FTM tool
  → WMI_PDEV_UTF_CMDID (command + payload)
    → WPSS blob processes command
      → WMI_PDEV_UTF_EVENTID (response or fragmented data)
        → Host reassembles if fragmented
          → Userspace via nl80211 or ioctl
```

---

## 9. Complete Initialization Summary

This is the full sequence a re-implemented blob must support, from
power-on to operational WiFi:

```
Phase 1 — Boot / PIL
────────────────────
  [TrustZone] PIL auth → load wpss.mbn → reset DSP → release reset
  [Firmware]   Initialize Hexagon RTOS, configure CE regs, assert WLAN_EN

Phase 2 — HIF
─────────────
  [Driver]  hif_bus_open() → SNOC → map MMIO BAR → init CE rings

Phase 3 — HTC
─────────────
  H2T: HTC_MSG_READY
  T2H: HTC_READY_MSG (credits, max endpoints, credit size)
  H2T: HTC_MSG_CONNECT_SERVICE_ID {WMI_CONTROL_SVC, HTT_DATA_MSG_SVC, ...}
  T2H: HTC_MSG_CONNECT_SERVICE_RESPONSE_ID (for each service)
  H2T: HTC_MSG_SETUP_COMPLETE_ID
  T2H: HTC_MSG_SETUP_COMPLETE_EX_ID

Phase 4 — WMI (Control)
───────────────────────
  T2H: WMI_SERVICE_READY_EVENTID (firmware version, service bitmap, capabilities)
  T2H: WMI_READY_EVENTID (PHY capabilities, build info)
  H2T: WMI_INIT_CMDID (host capabilities)
  H2T: WMI_VDEV_CREATE_CMDID (create virtual device)
  H2T: WMI_VDEV_UP_CMDID (bring vdev up)

Phase 5 — HTT (Data)
────────────────────
  H2T: HTT_H2T_MSG_TYPE_VERSION_REQ (negotiate HTT version)
  T2H: HTT_T2H_MSG_TYPE_VERSION_CONF
  H2T: HTT_H2T_MSG_TYPE_FRAG_DESC_BANK_CFG (TX fragment DMA region)
  H2T: HTT_H2T_MSG_TYPE_RX_RING_CFG (RX ring base + size)
  [Optional] H2T: HTT_H2T_MSG_TYPE_WDI_IPA_CFG (IPA offload)

Phase 6 — Operational
─────────────────────
  T2H: HTT_T2H_MSG_TYPE_PEER_MAP (as stations associate)
  H2T: HTT_H2T_MSG_TYPE_TX_FRM (transmit frames)
  T2H: HTT_T2H_MSG_TYPE_RX_IND (receive frames)
  T2H: HTT_T2H_MSG_TYPE_TX_COMPL_IND (transmit completion)
```

---

## 10. What a Re-implemented Blob Must Implement

### Minimum Viable Blob (data path only)

| Layer | Must Support |
|-------|--------------|
| **PIL** | None (TrustZone handles auth — blob just needs to execute) |
| **CE/MMIO** | Register layout matching `hif/src/ce/ce_reg.h` |
| **HIF** | MMIO BAR at WPSS base address |
| **HTC** | Control endpoint (0) + at least 4 service endpoints, credit flow control |
| **WMI** | `SERVICE_READY`, `READY`, `INIT_CMD` |
| **HTT** | Full handshake (VERSION → FRAG_DESC → RX_RING) + `TX_COMPL_IND` |
| **Data** | `TX_FRM` → transmit frame; `RX_IND` → received frame |

### Full Functional Blob

| Layer | Must Support |
|-------|--------------|
| **WMI** | All VDEV, PEER, SCAN, security (WEP/TKIP/AES-CCMP) commands and events |
| **HTT** | Aggregation (ADDBA/DELBA), flow control, multiple peers (>32) |
| **Data** | 802.11n/ac/ax frame formats (AMPDU, AMSDU), block ACK, QoS |
| **Stats** | `STATS_CONF`, `EXT_STATS_CONF` for debugging |
| **FTM** | `WMI_PDEV_UTF_CMDID` for calibration/testing (optional) |

---

## 11. Key Differences: WCN6750 vs Other QCA Chips

| Feature | WCN6750 (SNOC) | QCA6390/6490 (PCIe) | QCN7605 (PCIe) |
|---------|----------------|---------------------|----------------|
| Bus | SNOC (AHB) | PCIe Gen2 | PCIe Gen2 |
| CE count | 9 | 9 | 9 |
| HTT version | 3.75+ | 3.75+ | 3.75+ |
| Max peers | ~32 | ~512 | ~512 |
| MMIO | Platform BAR | PCI BAR | PCI BAR |
| IRQ | Platform IRQ | MSI-X | MSI-X |

The protocol layers (HTC, WMI, HTT) are **identical**. Only the HIF
transport differs. A re-implemented blob for WCN6750 could potentially
be adapted for PCIe chips by replacing the HIF/CE layer.

---

## 12. References

- `docs/htt.md` — HTT protocol specification (message formats, handshake)
- `docs/hif.md` — HIF/SNOC architecture (vtable, SNOC vs PCIe)
- `docs/CopyEngine.md` — CE pipe configuration and DMA ring management
- `docs/ath11k.md` — Stack layer overview (HDD → WMI → HTT → HIF)
- `docs/ftm.md` — FTM/UTF test mode interface
- `docs/wpss.b12.md` — Secure Boot certificate chain analysis
- `fw-api/fw/htt.h` — HTT protocol (~19,000 lines, canonical spec)
- `fw-api/fw/wmi.h` — WMI protocol definitions
- `fw-api/fw/wmi_unified.h` — WMI command/event ID enumeration
- `fw-api/fw/htc.h` — HTC frame format and control messages
- `fw-api/fw/htc_services.h` — Service ID definitions
- `hif/src/ce/ce_assignment.h` — CE pipe configurations per chip
- `hif/src/ce/ce_reg.h` — CE register layout
- `hif/src/dispatcher/multibus.c` — HIF bus dispatcher
- `hif/src/snoc/if_snoc.c` — SNOC bus implementation
