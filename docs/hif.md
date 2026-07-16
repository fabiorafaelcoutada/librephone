# HIF — Host Interface layer for WCN6750 (SNOC/fake-PCI)

## Overview

The **HIF** (Host Interface) is the transport abstraction layer between the
WLAN driver (qcacld-3.0) and the WPSS (WiFi Processor SubSystem) firmware.
On the WCN6750 (`QCA6750`, codename "Moselle"), the physical transport is
**SNOC** (System Network-on-Chip), an AHB-based interconnect built into the
Qualcomm SoC fabric. There is **no PCI bus involved** — the WPSS firmware
presents a *platform device* that the driver probes via the PLD (Platform
Driver) layer.

> **Key insight:** The term "fake PCI" refers to the fact that at the platform
> level, the WPSS firmware emulates a PCI-like programming model (MMIO BAR,
> CE registers, interrupt lines) over SNOC. The kernel ath11k driver sees a
> `pci_device_id` with VID `0x17cb` and DID `0x1105`, but no PCI enumeration
> ever happens — it's all SNOC underneath.

## Architecture

```
┌─────────────────────────────────────────┐
│  HTC — Host-Target Communication Layer  │  htc.c / htc_send()
├─────────────────────────────────────────┤
│  HIF Public API                         │  hif.h
│  hif_handle_t (opaque)                  │  hif_read_write(), hif_map_service()
├─────────────────────────────────────────┤
│  hif_main.c — shared dispatch           │  hif_softc, hif_bus_configure()
│  hif_main.h — struct hif_softc          │
├─────────────────────────────────────────┤
│  multibus.c — bus type dispatcher       │  hif_bus_open() switch(bus_type)
│  multibus.h — struct hif_bus_ops        │  vtable of ~40 function pointers
├──────────────────┬──────────────────────┤
│  SNOC (WCN6750)  │  PCI (QCA6390/etc)  │
│  if_snoc.c       │  if_pci.c           │
│  snoc/ce_tasklet │  pcie/if_pci.h      │
├──────────────────┴──────────────────────┤
│  CE — Copy Engine layer                 │  ce_main.c / ce_api.h
│  struct HIF_CE_state                    │  HIF_CE_pipe_info[12]
├─────────────────────────────────────────┤
│  MMIO (Memory-Mapped I/O)               │  hif_read32_mb / hif_write32_mb
│  hif_io32.h                             │  WPSS-provided base address
└─────────────────────────────────────────┘
```

## Source files

All paths relative to `qca-wifi-host-cmn/hif/` in the
[sm7635-modules](https://github.com/rsavoye/sm7635-modules) repository.

### Core HIF layer (`hif/`)

| File | Purpose |
|------|---------|
| `inc/hif.h` | Public API — types, `hif_handle_t`, `HIF_TYPE_QCA6750 = 23` |
| `inc/target_type.h` | `TARGET_TYPE_QCA6750 = 28` (Moselle) |
| `src/hif_main.h` | Core `struct hif_softc`, internal helpers |
| `src/hif_main.c` | Shared logic — init, dump, target ID, enable/disable |
| `src/hif_io32.h` | MMIO helpers: `hif_read32_mb()`, `hif_write32_mb()` |
| `src/hif_napi.c` | NAPI polling for RX data path |
| `src/hif_irq_affinity.c` | IRQ affinity for multi-core |
| `src/hif_exec.c` | Execution context (tasklet/NAPI dispatch) |
| `src/hif_debug.h` | Debug logging macros |
| `src/qca6750def.c` | **QCA6750 register definitions** — most marked `MISSING` |

### SNOC implementation (`hif/src/snoc/`)

| File | Purpose |
|------|---------|
| `snoc/if_snoc.c` | SNOC open, close, configure, suspend/resume, ISR, enable/disable |
| `snoc/if_ahb.c` | AHB bus variant (shared CE framework with SNOC) |
| `snoc/if_ahb.h` | AHB header |
| `snoc/hif_io32_snoc.h` | SNOC I/O — `ce_enable_irq_in_individual_register()` |

### CE — Copy Engine (`hif/src/ce/`)

| File | Purpose |
|------|---------|
| `ce/ce_main.h` | `struct HIF_CE_state`, `struct HIF_CE_pipe_info`, `struct ce_stats` |
| `ce/ce_main.c` | CE init, destroy, ring management, interrupt registration |
| `ce/ce_api.h` | Public API — `ce_send_cb`, `CE_recv_cb`, `ce_send()`, `ce_recv()` |
| `ce/ce_internal.h` | Internal: `CE_ring_state`, `CE_op_state`, ring indices |
| `ce/ce_bmi.c` | BMI (Boot Memory Interface) over CE — not used on SNOC |
| `ce/ce_service.c` | CE service layer |
| `ce/ce_service_srng.c` | CE service for SRNG-based targets |
| `ce/ce_tasklet.c` | **ISR for SNOC**: `hif_snoc_interrupt_handler()` → tasklet dispatch |
| `ce/ce_reg.h` | CE register layout definitions |
| `ce/ce_assignment.h` | CE ID → service mapping |
| `ce/ce_diag.c` | Diagnostic access over CE |

### Dispatcher (`hif/src/dispatcher/`)

| File | Purpose |
|------|---------|
| `dispatcher/multibus.c` | `hif_bus_open()` — main entry, dispatches by `qdf_bus_type` |
| `dispatcher/multibus.h` | `struct hif_bus_ops` — **the operation vtable** |
| `dispatcher/multibus_snoc.c` | `hif_initialize_snoc_ops()` — assigns SNOC implementations |
| `dispatcher/multibus_pci.c` | `hif_initialize_pci_ops()` — PCI (not used on WCN6750) |
| `dispatcher/multibus_ahb.c` | `hif_initialize_ahb_ops()` — AHB (variant) |
| `dispatcher/snoc_api.h` | SNOC function declarations |
| `dispatcher/dummy.c` | Dummy implementations for unsupported operations |
| `dispatcher/dummy.h` | `hif_dummy_set_mailbox_swap()`, etc. — no-ops |

### Key data structures

#### `struct hif_softc` (hif_main.h)

The primary HIF context passed through all layers:

| Field | Type | Description |
|-------|------|-------------|
| `mem` | `void *` | MMIO base (virtual), set by `pld_get_soc_info()` |
| `mem_pa` | `phys_addr_t` | MMIO base (physical) |
| `bus_type` | `enum qdf_bus_type` | `QDF_BUS_TYPE_SNOC` for WCN6750 |
| `bus_ops` | `struct hif_bus_ops` | The operation vtable (~40 function pointers) |
| `ce_id_to_state[12]` | `struct HIF_CE_state *` | Per-CE state pointers (CE 0..11) |
| `target_info` | `struct target_info` | Version, type, revision of target firmware |
| `ce_count` | `int` | Number of Copy Engines — 12 for WCN6750 |
| `wake_irq` | `int` | Wake interrupt number |
| `per_ce_irq` | `bool` | Whether each CE has its own IRQ line |
| `napi_data` | `struct hif_napi_data` | NAPI context for data-path polling |
| `callbacks` | `struct hif_driver_state_callbacks` | Driver state change hooks |

#### `struct HIF_CE_state` (ce/ce_main.h)

SNOC's runtime context — embeds `hif_softc`:

```c
struct HIF_CE_state {
    struct hif_softc ol_sc;                  // embedded base context
    struct ce_tasklet_entry tasklets[12];    // one tasklet per CE
    struct HIF_CE_pipe_info pipe_info[12];   // per-pipe metadata
    struct CE_pipe_config *target_ce_config; // FW-provided config
    struct CE_attr *host_ce_config;          // host-side config
    struct ce_ops *ce_services;              // CE service function table
    int sleep_timer_init;                    // sleep timer state
    // ... IRQ registration, runtime PM state
};
```

On SNOC, `hif_snoc_get_context_size()` returns `sizeof(struct HIF_CE_state)`.
PCI has an additional wrapper (`hif_pci_softc`) around this.

#### `struct hif_bus_ops` (dispatcher/multibus.h)

The operation vtable — ~40 function pointers. Key entries:

| Method | SNOC | PCI |
|--------|:----:|:---:|
| `hif_bus_open()` | `hif_snoc_open` | `hif_pci_open` |
| `hif_bus_close()` | `hif_snoc_close` | `hif_pci_close` |
| `hif_bus_configure()` | `hif_snoc_configure` | `hif_pci_configure` |
| `hif_bus_suspend()` | `hif_snoc_suspend` | `hif_pci_suspend` |
| `hif_bus_resume()` | `hif_snoc_resume` | `hif_pci_resume` |
| `hif_enable_bus()` | `hif_snoc_enable_bus` | `hif_pci_enable_bus` |
| `hif_disable_bus()` | `hif_snoc_disable_bus` | `hif_pci_disable_bus` |
| `hif_disable_isr()` | `hif_snoc_disable_isr` | `hif_pci_disable_isr` |
| `hif_irq_enable()` | `hif_snoc_irq_enable` | `hif_pci_irq_enable` |
| `hif_map_ce_to_irq()` | `hif_snoc_map_ce_to_irq` | `hif_pci_map_ce_to_irq` |
| `hif_dump_registers()` | `hif_snoc_dump_registers` | `hif_pci_dump_registers` |
| `hif_needs_bmi()` | returns `false` | returns `true` |
| `hif_set_mailbox_swap()` | **dummy (no-op)** | real implementation |
| `hif_reset_soc()` | **dummy (no-op)** | real implementation |
| `hif_reg_read32/reg_write32` | **dummy** | windowed PCI I/O |

### Copy Engine assignments (hardcoded for WCN6750)

The CE layer handles DMA between host memory and WPSS shared memory.
Each CE has a source ring and destination ring.

| CE ID | Service | Direction | Description |
|:-----:|---------|:---------:|-------------|
| 0 | `HTC_CTRL` | Host → Target | Control messages (WMI) |
| 1 | `HTT_DATA2_MSG` | Target → Host | **HTT T2H (RX data)** — primary RX path |
| 2 | `WMI_LOGS` | Target → Host | Firmware logs / diag |
| 3 | `PKTLOG` | Target → Host | Packet logging |
| 4 | `HTT_H2T_MSG` | Host → Target | **HTT H2T (TX config)** — ring configs, frag desc |
| 5 | `HTC_DATA` | Bidirectional | Data path (alternative) |
| 6 | `HTC_DATA` | Bidirectional | Data path (alternative) |
| 7 | `HTC_DATA` | Bidirectional | Data path (alternative) |
| 8 | `TARGET_TO_HOST` | Target → Host | Generic (WMI events, diag) |
| 9 | `WMI_CTRL_DIAG` | Target → Host | WMI control diag |
| 10 | `HTC_DATA` | Bidirectional | Data path (alternative) |
| 11 | `TARGET2HOST_MSG` | Target → Host | Target-to-host notification |

> Source: `ce_assignment.h`, cross-referenced with HTT docs at
> `fw-api/fw/htt.h` lines defining `CE_HTT_T2H_MSG = 1` and `CE_HTT_H2T_MSG = 4`.

## SNOC vs PCI comparison

| Aspect | SNOC (WCN6750) | PCI (QCA6390, QCN9074) |
|--------|:-------------:|:---------------------:|
| **Bus type** | `QDF_BUS_TYPE_SNOC` | `QDF_BUS_TYPE_PCI` |
| **Device probe** | Platform device via PLD | PCI enumeration (VID/DID) |
| **MMIO base** | Pre-mapped by WPSS firmware (`soc_info.v_addr`) | `ioremap()` of PCI BAR |
| **Interrupt model** | Per-CE IRQ via platform bus | MSI/MSI-X or legacy INTx |
| **Context struct** | `struct HIF_CE_state` | `struct hif_pci_softc` (wraps `HIF_CE_state`) |
| **BMI required** | No — firmware handles boot | Yes — driver does BMI via CE |
| **Sleep/wake** | `enable_irq_wake()` on wake CE | `PCIE_SOC_WAKE` register + force wake |
| **Suspend behavior** | Bus stays on, target can sleep | PCI link enters L1/L2 states |
| **Dummy ops count** | ~15 method pointers are no-op dummies | 0 (all ops implemented) |
| **CE_COUNT** | 12 | 12 |
| **Max message size** | 256 descriptors × 256 bytes = 64 KB (HTT) | Same |

## Initialization flow

```
1. pld_get_soc_info()          — PLD layer obtains MMIO base + IRQs from WPSS
   ├→ v_addr = WPSS-shared memory base
   └→ irq_count = 12 per-CE interrupts

2. hif_open()                  — Allocates hif_softc or HIF_CE_state
   └→ hif_snoc_get_context_size() → sizeof(HIF_CE_state)

3. hif_bus_open(QDF_BUS_TYPE_SNOC)
   ├→ hif_initialize_default_ops(hif_sc)     // all ops = dummies
   ├→ switch(bus_type) → hif_initialize_snoc_ops(&hif_sc->bus_ops)
   ├→ hif_verify_basic_ops(hif_sc)           // ensure no NULLs
   └→ hif_sc->bus_ops.hif_bus_open()         // → hif_snoc_open()

4. hif_snoc_open()
   ├→ Copy CE config from target (CE_pipe_config read from WPSS shared mem)
   ├→ hif_ce_open() — init each CE
   │   ├→ Allocate source + destination rings
   │   ├→ Register ce_tasklet for each CE (→ hif_snoc_interrupt_handler)
   │   └→ Set CE state → CE_RUNNING
   ├→ Register IRQs (per-CE or single shared)
   └→ Enable bus → HIF_SYSTEM_PM_STATE_ON

5. hif_enable_bus()
   └→ hif_sc->bus_ops.hif_enable_bus() → hif_snoc_enable_bus()
       └→ hif_snoc_init_registers() via hif_io32_snoc.h macros
```

## Interrupt handling — SNOC data path

```
Hardware IRQ (per-CE)
  → hif_snoc_interrupt_handler()   // ce_tasklet.c
    → hif_nointrs()                // mask further interrupts
    → ce_per_engine_service()      // process the CE that fired
      → ce_recv_cb()               // if RX: drain RX ring → HTC/HTT callback
      → ce_send_cb()               // if TX: free completed TX descriptors
    → schedule ce_tasklet          // defer to tasklet for batched processing
    → hif_irq_enable()             // re-enable interrupts
```

## QCA6750 register map (qca6750def.c)

Most hardware registers are defined as `MISSING` — meaning the WPSS firmware
abstracts them and the host driver doesn't need to program them directly.
The critical registers that are defined:

| Register | Description |
|----------|-------------|
| `WFSS_CE_COMMON_R0_CE_HOST_IE_0` | Interrupt enable for CE 0..7 |
| `WFSS_CE_COMMON_R0_CE_HOST_IE_1` | Interrupt enable for CE 8..11 |
| `CE_WRAPPER_*` | Ring base addresses, indices per CE |
| `MISC_CONTROL_STATUS` | Global status register |

All PHY/MAC/RX/TX registers (the bulk of `qca6750def.c`) are `MISSING` —
they belong to the WPSS internal address space.

## Key constants

```c
// From hif.h
#define HIF_TYPE_QCA6750      23      // HIF device type identifier
#define HIF_DEVICE_ID_QCA6750 0x1105  // "PCI device ID" (fake PCI)

// From target_type.h
#define TARGET_TYPE_QCA6750   28      // Codename "Moselle"

// From ce_main.h
#define CE_COUNT_MAX          12      // CE 0..11
#define CE_HTT_T2H_MSG         1      // HTT Target→Host (RX)
#define CE_HTT_H2T_MSG         4      // HTT Host→Target (TX)

// CE operational states (ce_internal.h)
enum CE_op_state {
    CE_UNUSED,      // Not initialized
    CE_PAUSED,      // Initialized but stopped
    CE_RUNNING,     // Active — rings are being processed
    CE_PENDING,     // Transitional state
};
```

## HIF System PM states

```c
enum hif_system_pm_state {
    HIF_SYSTEM_PM_STATE_ON,              // Bus fully operational
    HIF_SYSTEM_PM_STATE_BUS_RESUMING,    // Transitioning from suspend
    HIF_SYSTEM_PM_STATE_BUS_SUSPENDING,  // Transitioning to suspend
    HIF_SYSTEM_PM_STATE_BUS_SUSPENDED,   // Bus suspended
};
```

On SNOC, the bus stays in `ON` state even when the target sleeps — there's
no PCI link power management. Wake is handled by `enable_irq_wake()` on
the wake-capable CE instead of PCI `PCIE_SOC_WAKE` register toggling.
