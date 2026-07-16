# HTT — Host-to-Target Transport Protocol

**Sources analyzed:**
- `fw-api/fw/htt.h` (primary spec, ~19 000 lines) — from Qualcomm WCN6750 open-source release
- `qcacld-3.0/core/dp/htt/htt_h2t.c` — H2T message handlers
- `qcacld-3.0/core/dp/htt/htt.c` — HTT initialization and T2H dispatch
- `qca-wifi-host-cmn/hif/src/ce/ce_main.h` — Copy Engine pipe definitions

> These files are part of the Qualcomm open-source host driver for
> WCN6750 (SM7635 SoC) released by Fairphone under ISC license.
> Repository: [ArianK16a/android_kernel_fairphone_sm7635-modules](https://github.com/ArianK16a/android_kernel_fairphone_sm7635-modules) (branch `lineage-23.2`)

---

## Overview

HTT (Host-to-Target Transport) is the data-path messaging layer between the host driver and the WPSS blob. It sits **below WMI** (which handles control/configuration) and operates over Copy Engine pipes 1 and 4.

HTT is bidirectional:
- **H2T** (Host→Target/blob): commands, configuration, TX frames
- **T2H** (Target/blob→Host): acknowledgements, RX indications, TX completions, status reports

The protocol is defined in `fw-api/fw/htt.h`. This file is part of the Qualcomm open-source release and represents the contractual API that any re-implemented blob must support.

---

## Physical Transport: Copy Engine Pipes

HTT messages are carried by specific Copy Engine (CE) pipes. For the WCN6750:

| CE Pipe | Direction | Purpose |
|---------|-----------|---------|
| CE 1 | Target → Host | HTT T2H messages + HTC control |
| CE 4 | Host → Target | HTT H2T messages |

Defined in `qca-wifi-host-cmn/hif/src/ce/ce_main.h`:
```c
#define CE_HTT_T2H_MSG   1   /* T2H: blob sends to host via CE1 */
#define CE_HTT_H2T_MSG   4   /* H2T: host sends to blob via CE4 */
```

Each message is a DMA buffer. The header occupies `HTC_HTT_TRANSFER_HDRSIZE = 24` bytes.

---

## Initialization Handshake

The function `htt_attach_target()` in `qcacld-3.0/core/dp/htt/htt.c:662` defines
the mandatory initialization sequence. The blob must respond to each step before
the host continues:

```
Host (driver)                           Target (blob / WCN6750)
─────────────────────────────────────────────────────────────────
  H2T VERSION_REQ (0x0)         →
                                 ←      T2H VERSION_CONF (0x0)
  H2T FRAG_DESC_BANK_CFG (0x6)  →      (fragment descriptor bank address)
  H2T RX_RING_CFG (0x2)         →      (RX ring base address + size)
  H2T IPA_CFG (0x8)             →      (optional: IPA offload, if enabled)
─────────────────────────────────────────────────────────────────
  HTT channel is operational
```

### Step 1 — VERSION_REQ / VERSION_CONF

The first message ever sent to the blob. The host sends its expected HTT version;
the blob replies with the version it supports. If versions are incompatible the
host aborts initialization.

**H2T `VERSION_REQ` (type 0x0)** — `htt_h2t_ver_req_msg()`:
```c
*msg_word = 0;
HTT_H2T_MSG_TYPE_SET(*msg_word, HTT_H2T_MSG_TYPE_VERSION_REQ);
/* optional TLV: HTT_OPTION_TLV_TAG_MAX_TX_QUEUE_GROUPS */
```

**T2H `VERSION_CONF` (type 0x0)** — blob response:
The blob fills in its major/minor version numbers. The host does NOT wait for
this before sending the next messages — it assumes compatibility and proceeds
immediately. This is noted in the source comment:

> "The host could wait for the HTT version number confirmation message from the
> target before sending any further HTT messages, but it's reasonable to assume
> that the host and target HTT version numbers match."

### Step 2 — FRAG_DESC_BANK_CFG (0x6)

Communicates the physical address and size of the fragment descriptor bank —
a pre-allocated DMA region the blob uses to scatter TX frames.

### Step 3 — RX_RING_CFG (0x2)

Configures the RX ring: physical base address, number of entries, entry size,
and which fields to include in the RX descriptor. This tells the blob where
to DMA received frames into host memory.

### Step 4 — IPA offload (0x8, optional)

Only sent if `CONFIG_IPA_OFFLOAD` is enabled. Configures the Qualcomm IPA
(Intelligent Peripheral Accelerator) for hardware RX offload to modem.

---

## Bit-field Layout of Initialization Messages

All words are 32-bit little-endian. Bit ranges are written `[hi:lo]`.
Physical addresses are 32-bit (`HTT_PADDR64 = 0`) or 64-bit (`HTT_PADDR64 = 1`)
depending on the build flag. The WCN6750 on sm7635 uses 64-bit addresses.

Source: `fw-api/fw/htt.h` lines 984–1012 (VERSION_REQ), 12323–12394 (VERSION_CONF),
3753–3976 (RX_RING_CFG), 18215–18401 (FRAG_DESC_BANK_CFG).

---

### Message 1 — H2T `VERSION_REQ` (type 0x0)

Total size: 4 bytes (1 word) + optional TLVs.

```
 31            24  23            16  15             8  7              0
 ┌───────────────────────────────────────────────────┬───────────────┐
 │                      reserved                     │   msg_type    │  word 0
 └───────────────────────────────────────────────────┴───────────────┘
```

| Field      | Bits  | Value / Description                        |
|------------|-------|--------------------------------------------|
| `msg_type` | [7:0] | `0x00` — `HTT_H2T_MSG_TYPE_VERSION_REQ`   |
| reserved   | [31:8]| must be 0                                  |

Optional TLVs appended after word 0 (one per type, in any order):

| TLV tag | Purpose |
|---------|---------|
| `HTT_OPTION_TLV_TAG_HL_SUPPRESS_TX_COMPL_IND` | Request TX completion suppression |
| `HTT_OPTION_TLV_TAG_MAX_TX_QUEUE_GROUPS`       | Request N TX queue groups         |
| `HTT_OPTION_TLV_TAG_TCL_METADATA_VER`          | Declare supported TCL metadata ver |

Macro: `HTT_H2T_MSG_TYPE_SET(word, HTT_H2T_MSG_TYPE_VERSION_REQ)` — sets bits [7:0].

---

### Message 2 — T2H `VERSION_CONF` (type 0x0)

Total size: 4 bytes (1 word) + optional TLVs.

```
 31            24  23            16  15             8  7              0
 ┌───────────────┬───────────────┬───────────────────┬───────────────┐
 │   reserved    │  ver_major    │     ver_minor     │   msg_type    │  word 0
 └───────────────┴───────────────┴───────────────────┴───────────────┘
```

| Field       | Bits    | Mask         | Description                                      |
|-------------|---------|--------------|--------------------------------------------------|
| `msg_type`  | [7:0]   | `0x000000ff` | `0x00` — `HTT_T2H_MSG_TYPE_VERSION_CONF`        |
| `ver_minor` | [15:8]  | `0x0000ff00` | Minor HTT version supported by blob             |
| `ver_major` | [23:16] | `0x00ff0000` | Major HTT version — incompatible if mismatch    |
| reserved    | [31:24] | `0xff000000` | must be 0                                        |

Macros (from `htt.h:12371`):
```c
#define HTT_VER_CONF_MINOR_M  0x0000ff00  /* shift 8  */
#define HTT_VER_CONF_MAJOR_M  0x00ff0000  /* shift 16 */
```

Optional TLVs the blob appends to confirm host-requested options:

| TLV tag | Purpose |
|---------|---------|
| `HTT_OPTION_TLV_TAG_LL_BUS_ADDR_SIZE`          | 32- or 64-bit address mode in use |
| `HTT_OPTION_TLV_TAG_HL_SUPPRESS_TX_COMPL_IND`  | Confirm TX completion suppression |
| `HTT_OPTION_TLV_TAG_MAX_TX_QUEUE_GROUPS`        | Confirm N TX queue groups         |

> **Compatibility rule**: major version mismatch → abort; minor version
> mismatch → continue with the lower feature set. In practice the driver
> does not wait for VERSION_CONF before sending the next messages.

---

### Message 3 — H2T `FRAG_DESC_BANK_CFG` (type 0x6)

Communicates the DMA base address(es) and descriptor-ID ranges of the
fragment descriptor bank. The blob uses this to scatter TX frames without
the host passing the pointer each time.

Maximum banks supported: 4 (`HTT_TX_MSDU_EXT_BANK_MAX`).

#### Header word (word 0)

```
 31            24  23            16  15  11  10   9  8   7              0
 ┌───────────────┬───────────────┬───────┬───┬────┬───────────────────┐
 │   desc_size   │   num_banks   │  res  │SWP│PDEV│     msg_type      │
 └───────────────┴───────────────┴───────┴───┴────┴───────────────────┘
```

| Field       | Bits    | Mask         | Description                                          |
|-------------|---------|--------------|------------------------------------------------------|
| `msg_type`  | [7:0]   | `0x000000ff` | `0x06` — `HTT_H2T_MSG_TYPE_FRAG_DESC_BANK_CFG`    |
| `pdev_id`   | [9:8]   | `0x00000300` | Physical device ID (pdev index)                     |
| `swap`      | [10]    | `0x00000400` | 1 = byte-swap descriptor contents                   |
| reserved    | [15:11] | `0x0000f800` | must be 0                                           |
| `num_banks` | [23:16] | `0x00ff0000` | Number of banks being configured (1–4)              |
| `desc_size` | [31:24] | `0xff000000` | Size of each MSDU_EXT descriptor, in bytes          |

Macros (from `htt.h:18294`):
```c
#define HTT_H2T_FRAG_DESC_BANK_PDEVID_M    0x00000300  /* shift  8 */
#define HTT_H2T_FRAG_DESC_BANK_SWAP_M      0x00000400  /* shift 10 */
#define HTT_H2T_FRAG_DESC_BANK_NUM_BANKS_M 0x00ff0000  /* shift 16 */
#define HTT_H2T_FRAG_DESC_BANK_DESC_SIZE_M 0xff000000  /* shift 24 */
```

#### Per-bank base address (repeated N = num_banks times)

**32-bit mode** (HTT_PADDR64 = 0):
```
 ┌───────────────────────────────────────────────────────────────────┐
 │              BANKx_BASE_ADDRESS [31:0]                            │  +1 word
 └───────────────────────────────────────────────────────────────────┘
```

**64-bit mode** (HTT_PADDR64 = 1, used by WCN6750):
```
 ┌───────────────────────────────────────────────────────────────────┐
 │              BANKx_BASE_ADDRESS_LO [31:0]                         │  +1 word
 ├───────────────────────────────────────────────────────────────────┤
 │              BANKx_BASE_ADDRESS_HI [31:0]                         │  +1 word
 └───────────────────────────────────────────────────────────────────┘
```

#### Per-bank ID range (repeated N times, after all base addresses)

```
 31            16  15             0
 ┌───────────────┬────────────────┐
 │  BANKx_MAX_ID │  BANKx_MIN_ID  │  bank_info[x]
 └───────────────┴────────────────┘
```

| Field         | Bits    | Mask         | Description                            |
|---------------|---------|--------------|----------------------------------------|
| `BANKx_MIN_ID`| [15:0]  | `0x0000ffff` | First MSDU_EXT descriptor ID in bank x |
| `BANKx_MAX_ID`| [31:16] | `0xffff0000` | Last MSDU_EXT descriptor ID in bank x  |

Total message size (64-bit, N banks): `4 + N×8 + N×4 = 4 + 12N` bytes.
For N = 4: **52 bytes**.

---

### Message 4 — H2T `RX_RING_CFG` (type 0x2)

Tells the blob where in host memory to DMA received frames and which
descriptor fields to include. Covers 1 or 2 rings.

#### Header word (word 0)

```
 31            16  15             8  7              0
 ┌───────────────┬────────────────┬────────────────┐
 │   reserved    │   num_rings    │    msg_type    │
 └───────────────┴────────────────┴────────────────┘
```

| Field       | Bits   | Mask         | Description                        |
|-------------|--------|--------------|------------------------------------|
| `msg_type`  | [7:0]  | `0x000000ff` | `0x02` — `HTT_H2T_MSG_TYPE_RX_RING_CFG` |
| `num_rings` | [15:8] | `0x0000ff00` | Number of rings: 1 or 2           |
| reserved    | [31:16]| `0xffff0000` | must be 0                          |

Macro: `#define HTT_RX_RING_CFG_NUM_RINGS_M 0xff00  /* shift 8 */`

#### Per-ring payload (repeated num_rings times)

**Shadow register address** (FW_IDX write-back target):

| 64-bit mode | 32-bit mode |
|-------------|-------------|
| `IDX_SHADOW_REG_PADDR_LO [31:0]` | `IDX_SHADOW_REG_PADDR [31:0]` |
| `IDX_SHADOW_REG_PADDR_HI [31:0]` | — |

**Ring base address** (DMA target for RX buffers):

| 64-bit mode | 32-bit mode |
|-------------|-------------|
| `BASE_PADDR_LO [31:0]` | `BASE_PADDR [31:0]` |
| `BASE_PADDR_HI [31:0]` | — |

**Ring geometry word:**
```
 31            16  15             0
 ┌───────────────┬────────────────┐
 │    buf_sz     │    ring_len    │
 └───────────────┴────────────────┘
```
| Field      | Bits    | Description                              |
|------------|---------|------------------------------------------|
| `ring_len` | [15:0]  | Number of entries (buffer pointers) in ring |
| `buf_sz`   | [31:16] | Size of each RX buffer, in bytes         |

**Enable flags + initial index word:**
```
 31            16  15             0
 ┌───────────────┬────────────────┐
 │  idx_init_val │ enabled_flags  │
 └───────────────┴────────────────┘
```

| Flag bit | Field name          | Enables                        |
| --------:|--------------------|--------------------------------|
| [0]      | `ENABLED_802_11_HDR`| 802.11 header in descriptor    |
| [1]      | `ENABLED_MSDU_PAYLD`| MSDU payload                   |
| [2]      | `ENABLED_PPDU_START`| PPDU start descriptor          |
| [3]      | `ENABLED_PPDU_END`  | PPDU end descriptor            |
| [4]      | `ENABLED_MPDU_START`| MPDU start descriptor          |
| [5]      | `ENABLED_MPDU_END`  | MPDU end descriptor            |
| [6]      | `ENABLED_MSDU_START`| MSDU start descriptor          |
| [7]      | `ENABLED_MSDU_END`  | MSDU end descriptor            |
| [8]      | `ENABLED_RX_ATTN`   | RX attention word              |
| [9]      | `ENABLED_FRAG_INFO` | Fragment info table            |
| [10]     | `ENABLED_UCAST`     | Unicast frame delivery         |
| [11]     | `ENABLED_MCAST`     | Multicast frame delivery       |
| [12]     | `ENABLED_CTRL`      | Control frame delivery         |
| [13]     | `ENABLED_MGMT`      | Management frame delivery      |
| [14]     | `ENABLED_NULL`      | Null-data frame delivery       |
| [15]     | `ENABLED_PHY`       | PHY data delivery              |

`idx_init_val` [31:16]: initial value of the FW_IDX; equals the number of
buffers pre-filled by the host before signalling the blob.

**Descriptor field offset words** (5 words; offsets in quad-bytes from buffer start):

```
 31            16  15             0
 ┌───────────────┬────────────────┐
 │ MSDU_PAYLD off│ 802_11_HDR off │  word N+0
 ├───────────────┼────────────────┤
 │  PPDU_END off │  PPDU_START off│  word N+1
 ├───────────────┼────────────────┤
 │  MPDU_END off │  MPDU_START off│  word N+2
 ├───────────────┼────────────────┤
 │  MSDU_END off │  MSDU_START off│  word N+3
 ├───────────────┼────────────────┤
 │  FRAG_INFO off│   RX_ATTN off  │  word N+4
 └───────────────┴────────────────┘
```

Total per-ring payload: **36 bytes** (32-bit) / **44 bytes** (64-bit).
Total message: `4 + num_rings × payload_bytes`.

---

## H2T Message Types

Complete enum from `fw-api/fw/htt.h:918`. These are all the commands the
**host sends to the blob**. The blob must implement handlers for at least the
mandatory subset.

| Type ID | Name | Description |
|---------|------|-------------|
| 0x00 | `VERSION_REQ` | Version handshake — **mandatory, first message** |
| 0x01 | `TX_FRM` | Transmit a data frame |
| 0x02 | `RX_RING_CFG` | Configure RX descriptor ring — **mandatory** |
| 0x03 | `STATS_REQ` | Request firmware statistics |
| 0x04 | `SYNC` | Synchronization token |
| 0x05 | `AGGR_CFG` | A-MPDU aggregation configuration |
| 0x06 | `FRAG_DESC_BANK_CFG` | Fragment descriptor bank address — **mandatory** |
| 0x07 | ~~`MGMT_TX`~~ | Deprecated |
| 0x08 | `WDI_IPA_CFG` | IPA offload configuration |
| 0x09 | `WDI_IPA_OP_REQ` | IPA operation request |
| 0x0a | `AGGR_CFG_EX` | Per-vdev A-MSDU subframe limit |
| 0x0b | `SRING_SETUP` | Smart ring setup |
| 0x0c | `RX_RING_SELECTION_CFG` | RX ring selection configuration |
| 0x0d | `ADD_WDS_ENTRY` | Add WDS (4-addr) table entry |
| 0x0e | `DELETE_WDS_ENTRY` | Delete WDS table entry |
| 0x0f | `RFS_CONFIG` | Receive Flow Steering config |
| 0x10 | `EXT_STATS_REQ` | Extended statistics request |
| 0x11 | `PPDU_STATS_CFG` | Per-packet stats configuration |
| 0x12 | `RX_FSE_SETUP_CFG` | Flow Search Engine setup |
| 0x13 | `RX_FSE_OPERATION_CFG` | Flow Search Engine operation |
| 0x14 | `CHAN_CALDATA` | Channel calibration data |
| 0x15 | `RX_FISA_CFG` | Flow-Indication based SW Aggregation |
| 0x16 | `3_TUPLE_HASH_CFG` | 3-tuple hash config |
| 0x17 | `RX_FULL_MONITOR_MODE` | Full monitor mode config |
| 0x18 | `HOST_PADDR_SIZE` | Host physical address size |
| 0x19 | `RXDMA_RXOLE_PPE_CFG` | RXDMA/RXOLE PPE config |
| 0x1a | `VDEVS_TXRX_STATS_CFG` | Per-vdev TX/RX stats config |
| 0x1b | `TX_MONITOR_CFG` | TX monitor configuration |
| 0x1f | `MSI_SETUP` | MSI interrupt setup |
| 0x20 | `STREAMING_STATS_REQ` | Streaming stats request |
| 0x21 | `UMAC_HANG_RECOVERY_PREREQUISITE_SETUP` | UMAC hang recovery setup |
| 0x22 | `UMAC_HANG_RECOVERY_SOC_START_PRE_RESET` | UMAC hang recovery reset |
| 0x23 | `RX_CCE_SUPER_RULE_SETUP` | CCE classification super rule |
| 0x24 | `PRIMARY_LINK_PEER_MIGRATE_RESP` | MLO peer migration response |
| 0x25 | `TX_LATENCY_STATS_CFG` | TX latency statistics config |
| 0x26 | `TX_LCE_SUPER_RULE_SETUP` | TX LCE super rule setup |
| 0x27 | `SDWF_MSDUQ_RECFG_REQ` | MSDUQ reconfiguration request |
| 0x28 | `MLO_LATENCY_STATS_RESP` | MLO latency stats response |
| 0x29 | `MPDUQ_AND_MSDUQ_INFO_HDR` | MPDU/MSDU queue info header |
| 0x2a | `MPDUQ_OR_MSDUQ_INFO` | MPDU/MSDU queue info |

---

## T2H Message Types

Complete enum from `fw-api/fw/htt.h:12229`. These are all the messages the
**blob sends to the host**. The driver must implement handlers for these.
For a re-implemented blob, these are the messages it must be able to emit.

| Type ID | Name | Description |
|---------|------|-------------|
| 0x00 | `VERSION_CONF` | Version confirmation — **mandatory** |
| 0x01 | `RX_IND` | RX frame indication (legacy low-latency path) |
| 0x02 | `RX_FLUSH` | Flush RX reorder buffer |
| 0x03 | `PEER_MAP` | Map peer ID → MAC address |
| 0x04 | `PEER_UNMAP` | Unmap peer |
| 0x05 | `RX_ADDBA` | Add Block ACK session |
| 0x06 | `RX_DELBA` | Delete Block ACK session |
| 0x07 | `TX_COMPL_IND` | TX completion indication |
| 0x08 | `PKTLOG` | Packet log data |
| 0x09 | `STATS_CONF` | Statistics response |
| 0x0a | `RX_FRAG_IND` | RX fragment indication |
| 0x0b | `SEC_IND` | Security type indication |
| 0x0c | ~~`RC_UPDATE_IND`~~ | Deprecated |
| 0x0d | `TX_INSPECT_IND` | TX inspect (software fallback) |
| 0x0e | `MGMT_TX_COMPL_IND` | Management frame TX complete |
| 0x0f | `TX_CREDIT_UPDATE_IND` | TX credit update (HL path) |
| 0x10 | `RX_PN_IND` | RX packet number (replay protection) |
| 0x11 | `RX_OFFLOAD_DELIVER_IND` | Offloaded RX delivery |
| 0x12 | `RX_IN_ORD_PADDR_IND` | In-order RX physical address indication |
| 0x14 | `WDI_IPA_OP_RESPONSE` | IPA operation response |
| 0x15 | `CHAN_CHANGE` | Channel change notification |
| 0x16 | `RX_OFLD_PKT_ERR` | RX offload packet error |
| 0x17 | `RATE_REPORT` | Per-peer rate report |
| 0x18 | `FLOW_POOL_MAP` | Flow pool memory mapping |
| 0x19 | `FLOW_POOL_UNMAP` | Flow pool memory unmap |
| 0x1a | `SRING_SETUP_DONE` | Smart ring setup complete |
| 0x1b | `MAP_FLOW_INFO` | Flow info map |
| 0x1c | `EXT_STATS_CONF` | Extended stats response |
| 0x1d | `PPDU_STATS_IND` | Per-PPDU statistics indication |
| 0x1e | `PEER_MAP_V2` | Peer map version 2 (with AST info) |
| 0x1f | `PEER_UNMAP_V2` | Peer unmap version 2 |
| 0x20 | `MONITOR_MAC_HEADER_IND` | Monitor mode MAC header |
| 0x21 | `FLOW_POOL_RESIZE` | Flow pool resize notification |
| 0x22 | `CFR_DUMP_COMPL_IND` | Channel Frequency Response dump complete |
| 0x23 | `PEER_STATS_IND` | Per-peer statistics |
| 0x24 | `BKPRESSURE_EVENT_IND` | Back-pressure event |
| 0x25 | `TX_OFFLOAD_DELIVER_IND` | TX offload delivery (monitor mode) |
| 0x26 | `CHAN_CALDATA` | Channel calibration data |
| 0x27 | `FSE_CMEM_BASE_SEND` | Flow Search Engine CMEM base |
| 0x28 | `MLO_TIMESTAMP_OFFSET_IND` | MLO timestamp offset |
| 0x29 | `MLO_RX_PEER_MAP` | MLO RX peer map |
| 0x2a | `MLO_RX_PEER_UNMAP` | MLO RX peer unmap |
| 0x2b | `PEER_MAP_V3` | Peer map version 3 |
| 0x2c | `VDEVS_TXRX_STATS_PERIODIC_IND` | Periodic per-vdev TX/RX stats |
| 0x2d | `SAWF_DEF_QUEUES_MAP_REPORT_CONF` | SAWF queue map report |
| 0x2e | `SAWF_MSDUQ_INFO_IND` | SAWF MSDU queue info |
| 0x2f | `STREAMING_STATS_IND` | Streaming statistics |
| 0x30 | `PPDU_ID_FMT_IND` | PPDU ID format indication |
| 0x31 | `RX_ADDBA_EXTN` | Extended Add Block ACK |
| 0x32 | `RX_DELBA_EXTN` | Extended Delete Block ACK |
| 0x33 | `RX_CCE_SUPER_RULE_SETUP_DONE` | CCE rule setup complete |
| 0x35 | `RX_DATA_IND` | RX data indication (new path) |
| 0x36 | `SOFT_UMAC_TX_COMPL_IND` | Soft UMAC TX completion |
| 0x37 | `PRIMARY_LINK_PEER_MIGRATE_IND` | MLO primary link migration |
| 0x38 | `PEER_AST_OVERRIDE_INDEX_IND` | Peer AST override index |
| 0x39 | `PEER_EXTENDED_EVENT` | Extended peer event |
| 0x3a | `TX_LATENCY_STATS_PERIODIC_IND` | TX latency periodic stats |
| 0x3b | `TX_LCE_SUPER_RULE_SETUP_DONE` | TX LCE rule setup complete |
| 0x3c | `SDWF_MSDUQ_CFG_IND` | SDWF MSDUQ config |
| 0x3d | `MLO_LATENCY_REQ` | MLO latency request |
| 0x3e | `GLOBAL_PEER_ID_UNMAP` | Global peer ID unmap |
| 0x3f | `HAPS` | HAPS indication |

---

## Security Types

The blob handles per-peer security associations. Types defined in
`fw-api/fw/htt_common.h`:

| Value | Name |
|-------|------|
| 0 | `htt_sec_type_none` |
| 1 | `htt_sec_type_wep128` |
| 2 | `htt_sec_type_wep104` |
| 3 | `htt_sec_type_wep40` |
| 4 | `htt_sec_type_tkip` |
| 5 | `htt_sec_type_tkip_nomic` |
| 6 | `htt_sec_type_aes_ccmp` |
| 7 | `htt_sec_type_wapi` |
| 8 | `htt_sec_type_aes_ccmp_256` |
| 9 | `htt_sec_type_aes_gcmp` |
| 10 | `htt_sec_type_aes_gcmp_256` |

---

## T2H Message Handlers (driver side)

Source: `qcacld-3.0/core/dp/htt/htt_t2h.c`

The driver dispatches T2H messages in three functions with different
priority tiers. For a re-implemented blob this table shows exactly what
fields and callbacks the driver expects for each message it handles.

### Dispatch Architecture

```
CE1 interrupt
  └── htt_t2h_msg_handler()          normal path (HTC callback)
        ├── high-priority cases ──── handled inline (fast)
        └── default ──────────────── htt_t2h_lp_msg_handler()  (slow path)

CE fastpath
  └── htt_t2h_msg_handler_fast()     bypass HTC, CE-direct
```

### High-priority path — `htt_t2h_msg_handler()` (`htt_t2h.c:749`)

These are the most frequent messages; handled inline to minimize latency.

| Type ID | Name | Fields extracted | Callback |
|---------|------|-----------------|----------|
| 0x01 | `RX_IND` | `peer_id`[15:0], `tid`[7:0], `num_mpdu_ranges`, `num_msdu_bytes` | `ol_rx_indication_handler()` |
| 0x07 | `TX_COMPL_IND` | `status`[2:0], `num_msdus`[15:8], MSDU ID array (2B each) | `ol_tx_completion_handler()` |
| 0x10 | `RX_PN_IND` | `peer_id`, `tid`, `seq_num_start`, `seq_num_end`, `pn_ie[]` | `ol_rx_pn_ind_handler()` |
| 0x0d | `TX_INSPECT_IND` | `num_msdus`, MSDU ID array | `ol_tx_inspect_handler()` |
| 0x12 | `RX_IN_ORD_PADDR_IND` | `peer_id`, `tid`, `offload_ind`, `frag_ind` | `ol_rx_in_order_indication_handler()` / `ol_rx_frag_indication_handler()` |

> **TX_COMPL_IND endian note**: if `num_msdus` is odd, the driver checks
> `payload[num_msdus]` and may copy it to `payload[num_msdus-1]` to fix a
> host/firmware CPU endianness mismatch. The blob must be aware of this.

### Low-priority path — `htt_t2h_lp_msg_handler()` (`htt_t2h.c:217`)

Less frequent messages, dispatched from the `default:` arm of the main handler.

| Type ID | Name | Fields extracted | Callback / Action |
|---------|------|-----------------|-------------------|
| 0x00 | `VERSION_CONF` | `ver_major`[23:16], `ver_minor`[15:8] | Stores in `pdev->tgt_ver`; asserts major == `HTT_CURRENT_VERSION_MAJOR` |
| 0x02 | `RX_FLUSH` | `peer_id`, `tid`, `seq_num_start`, `seq_num_end`, `mpdu_status` | `ol_rx_flush_handler()` — release or discard reorder buffer |
| 0x03 | `PEER_MAP` | `peer_id`[15:0], `vdev_id`[7:0], MAC addr (words 1–2, deswizzled) | `ol_rx_peer_map_handler()` |
| 0x04 | `PEER_UNMAP` | `peer_id`[15:0] | `ol_rx_peer_unmap_handler()` |
| 0x05 | `RX_ADDBA` | `peer_id`, `tid`, `win_sz` | `ol_rx_addba_handler()` |
| 0x06 | `RX_DELBA` | `peer_id`, `tid` | `ol_rx_delba_handler()` |
| 0x08 | `PKTLOG` | raw payload (word 1+, length from nbuf) | `pktlog_process_fw_msg()` — conditional on `!REMOVE_PKT_LOG` |
| 0x09 | `STATS_CONF` | `cookie` (word 1, byte 0), `stats_info_list` (word 3+) | `ol_txrx_fw_stats_handler()` |
| 0x0a | `RX_FRAG_IND` | `peer_id`, `tid` (EXT_TID field) | `ol_rx_frag_indication_handler()` |
| 0x0b | `SEC_IND` | `peer_id`, `sec_type`[12:8], `is_unicast`[13], Michael key (words 1–2) | `ol_rx_sec_ind_handler()` |
| 0x0e | `MGMT_TX_COMPL_IND` | `htt_mgmt_tx_compl_ind` struct (word 1+): `desc_id`, `status` | `ol_tx_single_completion_handler()` (only if mgmt not over WMI) |
| 0x0f | `TX_CREDIT_UPDATE_IND` | `delta_abs`[31:16], `sign`[8], optional TX queue group TLV | `ol_tx_credit_completion_handler()` |
| 0x11 | `RX_OFFLOAD_DELIVER_IND` | `msdu_cnt`[15:0] | `ol_rx_offload_deliver_ind_handler()` |
| 0x14 | `WDI_IPA_OP_RESPONSE` | `rsp_len` (word 1 [15:0]), response payload | `htt_ipa_op_response()` |
| 0x16 | `RX_OFLD_PKT_ERR` | sub-type[7:0]; for MIC error: `peer_id`, `key_id`, PN (6 bytes at word 6) | `ol_rx_send_mic_err_ind()` |
| 0x18 | `FLOW_POOL_MAP` | `num_flows`, array of `htt_flow_pool_map_payload_t` | `ol_tx_flow_pool_map_handler()` per flow |
| 0x19 | `FLOW_POOL_UNMAP` | `htt_flow_pool_unmap_t`: `flow_id`, `flow_type`, `flow_pool_id` | `ol_tx_flow_pool_unmap_handler()` |
| 0x21 | `FLOW_POOL_RESIZE` | `htt_flow_pool_resize_t`: `flow_pool_id`, `flow_pool_new_size` | `ol_tx_flow_pool_resize_handler()` |
| 0x22 | `CFR_DUMP_COMPL_IND` | `htt_cfr_dump_compl_ind` struct | `ol_rx_cfr_capture_msg_handler()` — conditional on `WLAN_CFR_ENABLE` |

### Fast path — `htt_t2h_msg_handler_fast()` (`htt_t2h.c:1110`)

Used when CE fastpath is enabled (`WLAN_FEATURE_FASTPATH`). Handles the
same high-frequency messages as the normal path, plus one additional type:

| Type ID | Name | Notes |
|---------|------|-------|
| 0x01 | `RX_IND` | Same logic as normal path |
| 0x07 | `TX_COMPL_IND` | Same logic; no HL credit path |
| 0x25 | `TX_OFFLOAD_DELIVER_IND` | Packet capture monitor mode; only active if `PKT_CAPTURE_MODE_DATA_ONLY` → `ucfg_pkt_capture_offload_deliver_indication_handler()` |
| 0x10 | `RX_PN_IND` | Same logic as normal path |
| 0x0d | `TX_INSPECT_IND` | Same logic as normal path |
| 0x12 | `RX_IN_ORD_PADDR_IND` | Same logic as normal path |

### MAC address deswizzle

`PEER_MAP` uses a firmware-specific byte reordering for MAC addresses.
The driver calls `htt_t2h_mac_addr_deswizzle()` before passing the MAC
to the txrx layer. A re-implemented blob must use the same byte order
the existing blob uses — which matches the swizzle applied by
`htt_t2h_mac_addr_deswizzle()` in reverse.

---

## Gaps / Open Questions

1. ~~**Message structure details**~~ — **DONE**: bit-field layouts for all 4
   initialization messages (VERSION_REQ, VERSION_CONF, FRAG_DESC_BANK_CFG,
   RX_RING_CFG) are now documented in the section above. Source:
   `fw-api/fw/htt.h` lines 984, 12323, 18215, 3753.

2. ~~**Testing API**~~ — **DONE**: documented in [ftm.md](ftm.md). The
   testing API is the **FTM/UTF (Factory Test Mode / Unified Test Framework)**
   subsystem. It travels over **WMI** (not HTT) via `wmi_pdev_utf_cmd_id` /
   `wmi_pdev_utf_event_id`. Key files: `qca-wifi-host-cmn/ftm/` and
   `qca-wifi-host-cmn/target_if/ftm/`.

3. ~~**wpss.b12 certs**~~ — **DONE**: documented in [wpss_b12.md](wpss_b12.md).
   Three X.509 v3 certificates in DER format, loaded by the kernel PIL
   (`qcom_mdt_loader`) via SCM/TrustZone before WPSS boots. Separate from
   the executable segments — strategic importance for re-implementation.
   Open sub-questions: exact cert offsets, Root CA identity, SCM call ID.

4. ~~**T2H message handlers in the driver**~~ — **DONE**: documented in the
   section above. All handlers are in `qcacld-3.0/core/dp/htt/htt_t2h.c`
   across three dispatcher functions: `htt_t2h_msg_handler()` (normal path),
   `htt_t2h_lp_msg_handler()` (low priority), and
   `htt_t2h_msg_handler_fast()` (CE fastpath). 21 distinct message types
   handled; callbacks documented per type.
