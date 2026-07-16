# FTM — Factory Test Mode / UTF API

**Sources analyzed:**
- `qca-wifi-host-cmn/ftm/core/src/wlan_ftm_svc.c`
- `qca-wifi-host-cmn/ftm/core/src/wlan_ftm_svc_i.h`
- `qca-wifi-host-cmn/ftm/dispatcher/inc/wlan_ftm_ucfg_api.h`
- `qca-wifi-host-cmn/ftm/dispatcher/src/wlan_ftm_ucfg_api.c`
- `qca-wifi-host-cmn/target_if/ftm/src/target_if_ftm.c`
- `qca-wifi-host-cmn/target_if/ftm/inc/target_if_ftm.h`
- `qca-wifi-host-cmn/os_if/linux/ftm/inc/wlan_cfg80211_ftm.h`
- `qca-wifi-host-cmn/os_if/linux/ftm/src/wlan_cfg80211_ftm.c`
- `qca-wifi-host-cmn/os_if/linux/ftm/inc/wlan_ioctl_ftm.h`
- `qcacld-3.0/core/hdd/src/wlan_hdd_ftm.c`

---

## Overview

The FTM subsystem (also called **UTF — Unified Test Framework**) is the
low-level testing API Rob referred to in his email. It provides a raw
command/response channel between a userspace FTM daemon and the WCN6750
blob, used for RF calibration, production testing, and hardware diagnostics.

> **Key distinction from HTT**: FTM commands travel over **WMI** (Wireless
> Module Interface), not over the HTT data path. A re-implemented blob must
> handle `wmi_pdev_utf_event_id` WMI events in addition to the HTT
> initialization sequence.

FTM mode is only active when the driver is loaded with
`device_mode == QDF_GLOBAL_FTM_MODE` (as opposed to the normal station or AP
modes). In normal operation this subsystem is idle.

---

## Architecture

```
User space (FTM daemon / calibration tool)
  │
  ├─ via ioctl:     FTM_IOCTL_UNIFIED_UTF_CMD (0x1000)
  │                 FTM_IOCTL_UNIFIED_UTF_RSP  (0x1001)
  │                 → wlan_ioctl_ftm_testmode_cmd()
  │
  └─ via nl80211:   cfg80211 testmode (WLAN_CFG80211_FTM_CMD_WLAN_FTM = 0)
                    → wlan_cfg80211_ftm_testmode_cmd()
                    
          ↓  (both paths converge here)
          
  ucfg_wlan_ftm_testmode_cmd()          [dispatcher/ucfg layer]
          ↓
  wlan_ftm_cmd_send()                   [core service]
          ↓
  target_if_ftm_cmd_send()              [target_if — blob boundary]
          ↓
  wmi_unified_pdev_utf_cmd_send()       [WMI UTF command → blob]
          ↓
  ════════════════════════════════════  [BLOB / WCN6750]
          ↓
  wmi_pdev_utf_event_id                 [WMI UTF event ← blob]
          ↓
  target_if_ftm_process_utf_event()     [event handler]
          ↓
  wlan_ftm_process_utf_event()          [reassembly of fragments]
          ↓
  wlan_cfg80211_ftm_rx_event()          [back to user space via nl80211]
  ucfg_wlan_ftm_testmode_rsp()          [back to user space via ioctl]
```

---

## Command Entry Points

### ioctl path

```c
/* wlan_ioctl_ftm.h */
#define FTM_IOCTL_UNIFIED_UTF_CMD   0x1000   /* host → blob */
#define FTM_IOCTL_UNIFIED_UTF_RSP   0x1001   /* blob → host (poll) */
```

`wlan_ioctl_ftm_testmode_cmd(pdev, cmd, userdata)` — handles both ioctl
codes. `UTF_CMD` sends data to the blob; `UTF_RSP` polls for and copies
the buffered response.

### nl80211 / cfg80211 path

```c
/* wlan_cfg80211_ftm.h */
enum wlan_cfg80211_ftm_attr {
    WLAN_CFG80211_FTM_ATTR_CMD  = 1,   /* NLA_U32 — command type */
    WLAN_CFG80211_FTM_ATTR_DATA = 2,   /* NLA_BINARY — payload */
};

enum wlan_cfg80211_ftm_cmd {
    WLAN_CFG80211_FTM_CMD_WLAN_FTM = 0,
};

#define WLAN_FTM_DATA_MAX_LEN  2048
```

`wlan_cfg80211_ftm_testmode_cmd(pdev, data, len)` — parses the NLA
attributes, then calls into the same ucfg layer as the ioctl path.
Responses are pushed back asynchronously via `cfg80211_testmode_event()`.

---

## Constants

| Name | Value | Description |
|------|-------|-------------|
| `FTM_CMD_MAX_BUF_LENGTH` | 2048 | Max payload per command/response, in bytes |
| `WLAN_FTM_DATA_MAX_LEN`  | 2048 | Same limit at the nl80211 layer |
| `FTM_IOCTL_UNIFIED_UTF_CMD` | `0x1000` | ioctl command code (send) |
| `FTM_IOCTL_UNIFIED_UTF_RSP` | `0x1001` | ioctl command code (receive) |
| `WLAN_CFG80211_FTM_CMD_WLAN_FTM` | `0` | nl80211 FTM command type |

---

## Response Segmentation — `ftm_seg_hdr_info`

The blob may split large responses into multiple WMI events. Each event
carries a 16-byte segment header:

```c
/* wlan_ftm_svc_i.h */
struct ftm_seg_hdr_info {
    uint32_t len;           /* total length of the reassembled payload */
    uint32_t msgref;        /* message reference — ties fragments together */
    uint32_t segment_info;  /* [3:0] = current_seq, [7:4] = total_segments */
    uint32_t pad;           /* padding to align to 16 bytes */
};
```

| Field | Bits | Description |
|-------|------|-------------|
| `len` | [31:0] | Full length of the reassembled response |
| `msgref` | [31:0] | Opaque reference number linking all segments |
| `current_seq` | [3:0] of `segment_info` | 0-based index of this segment |
| `total_segments` | [7:4] of `segment_info` | Total number of segments expected |
| `pad` | [31:0] | Zero padding |

Reassembly in `wlan_ftm_process_utf_event()`:
1. `current_seq == 0` → reset `offset` and `expected_seq` to 0.
2. Copy `event_buf[sizeof(seghdr_info):]` into internal buffer at `offset`.
3. Advance `offset += utf_datalen`, increment `expected_seq`.
4. When `expected_seq == total_segments` → response complete; deliver to user.

---

## pdev Private Object — `wifi_ftm_pdev_priv_obj`

The driver allocates one of these per pdev (physical device) when entering
FTM mode:

```c
struct wifi_ftm_pdev_priv_obj {
    struct wlan_objmgr_pdev *pdev;
    uint8_t  *data;           /* reassembly buffer, FTM_CMD_MAX_BUF_LENGTH bytes */
    uint8_t   current_seq;    /* last received segment sequence number */
    uint8_t   expected_seq;   /* next expected sequence number */
    qdf_size_t length;        /* length of last complete response */
    qdf_size_t offset;        /* write offset into data[] during reassembly */
    enum wifi_ftm_pdev_cmd_type cmd_type;  /* IOCTL or NL80211 */
};
```

`cmd_type` tracks the origin of the command so the response is routed back
through the correct path (ioctl buffer vs cfg80211 event).

---

## What the Blob Must Implement

For a re-implemented WCN6750 firmware to support this API:

1. **Register handler for `wmi_pdev_utf_cmd_id`** — receive opaque UTF
   payloads from the host. The blob treats the payload as an opaque byte
   array (the driver does not parse it).

2. **Send responses as `wmi_pdev_utf_event_id` WMI events**, with each
   event prefixed by a `ftm_seg_hdr_info` (16 bytes). If the response fits
   in one event (`total_segments = 1`), `current_seq = 0`.

3. **Only be active in FTM mode** — normal station/AP operation does not
   use this channel.

4. **Respect the 2048-byte payload limit** per segment.

---

## Relationship to HTT

| Layer | Protocol | Used for |
|-------|----------|----------|
| HTT | Copy Engine (CE 1/4) | Normal data path — RX/TX frames |
| FTM/UTF | WMI | Factory testing, RF calibration |

Both must be implemented by a replacement blob, but they operate
independently. The FTM channel is only active in `QDF_GLOBAL_FTM_MODE`;
HTT is active in all other modes.

---

## Source File Map

| File | Role |
|------|------|
| `os_if/linux/ftm/src/wlan_cfg80211_ftm.c` | nl80211 entry point, NLA parsing |
| `os_if/linux/ftm/src/wlan_ioctl_ftm.c` | ioctl entry point |
| `ftm/dispatcher/src/wlan_ftm_ucfg_api.c` | ucfg dispatch + response reassembly |
| `ftm/core/src/wlan_ftm_svc.c` | pdev lifecycle, `wlan_ftm_cmd_send()` |
| `ftm/core/src/wlan_ftm_svc_i.h` | `ftm_seg_hdr_info` struct |
| `target_if/ftm/src/target_if_ftm.c` | WMI send/receive — blob boundary |

---

```
SPDX-License-Identifier: AGPL-3.0-or-later
```
