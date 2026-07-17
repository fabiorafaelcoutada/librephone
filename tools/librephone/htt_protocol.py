#!/usr/bin/env python3

# Copyright (c) 2026 Free Software Foundation, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""HTT (Host-Target Transport) protocol message lookup.

Protocol used in ath11k/WCN6750 for host <-> WPSS firmware communication.
Data extracted from the technical document `docs/htt.md` (branch `docs/htt-protocol`).

Usage:
    from tools.librephone.htt_protocol import lookup_htt_message, list_htt_messages

    msg = lookup_htt_message(0x00, "H2T")
    print(msg["name"])  # HTT_H2T_MSG_TYPE_VERSION_REQ

    all_msgs = list_htt_messages("H2T")
    print(f"{len(all_msgs)} known H2T messages")"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = [
    "HTTMessageNotFound",
    "lookup_htt_message",
    "list_htt_messages",
    "get_htt_handshake",
]


class HTTMessageNotFound(LookupError):
    """The requested HTT message ID is not in the known range."""


# ── H2T table (Host -> Target): 43 messages (0x00-0x2a) ────────────────────

_H2T_MESSAGES: List[Dict[str, Any]] = [
    {"id": 0x00, "name": "HTT_H2T_MSG_TYPE_VERSION_REQ",
     "desc": "HTT protocol version request. Initiates the handshake."},
    {"id": 0x01, "name": "HTT_H2T_MSG_TYPE_FRAG_DESC_BANK_CFG",
     "desc": "Configures fragment descriptor banks for RX."},
    {"id": 0x02, "name": "HTT_H2T_MSG_TYPE_RX_RING_CFG",
     "desc": "Configures DMA receive rings (RX rings)."},
    {"id": 0x03, "name": "HTT_H2T_MSG_TYPE_IPA_CFG",
     "desc": "Configures the IPA (IP Accelerator) interface."},
    {"id": 0x04, "name": "HTT_H2T_MSG_TYPE_IPA_OFFLOAD_CFG",
     "desc": "Configures IPA offloading."},
    {"id": 0x05, "name": "HTT_H2T_MSG_TYPE_6G_LNA_CHAIN",
     "desc": "Selects LNA chain for 6 GHz band."},
    {"id": 0x06, "name": "HTT_H2T_MSG_TYPE_FW_STATS_REQ",
     "desc": "Firmware statistics request."},
    {"id": 0x07, "name": "HTT_H2T_MSG_TYPE_GET_FW_STATS",
     "desc": "Gets detailed firmware statistics."},
    {"id": 0x08, "name": "HTT_H2T_MSG_TYPE_TX_FETCH_REQ",
     "desc": "Requests TX descriptors from host to target."},
    {"id": 0x09, "name": "HTT_H2T_MSG_TYPE_TX_FETCH_IND",
     "desc": "TX descriptors ready indication."},
    {"id": 0x0A, "name": "HTT_H2T_MSG_TYPE_TX_FETCH_CONF",
     "desc": "TX descriptors received confirmation."},
    {"id": 0x0B, "name": "HTT_H2T_MSG_TYPE_TX_FRAG",
     "desc": "Transfers TX frame fragments."},
    {"id": 0x0C, "name": "HTT_H2T_MSG_TYPE_TX_FRAG_DESC",
     "desc": "TX fragment descriptor."},
    {"id": 0x0D, "name": "HTT_H2T_MSG_TYPE_TX_OFFLOAD",
     "desc": "TX offloading request."},
    {"id": 0x0E, "name": "HTT_H2T_MSG_TYPE_TX_OFFLOAD_NORES",
     "desc": "TX offloading without additional resource."},
    {"id": 0x0F, "name": "HTT_H2T_MSG_TYPE_TX_FLOW_DELETE",
     "desc": "Deletes a TX flow."},
    {"id": 0x10, "name": "HTT_H2T_MSG_TYPE_TX_FLOW_DELETE_NO_RBM",
     "desc": "Deletes a TX flow without buffer return."},
    {"id": 0x11, "name": "HTT_H2T_MSG_TYPE_TX_FLOW_MGMT",
     "desc": "TX flow management (creation/modification)."},
    {"id": 0x12, "name": "HTT_H2T_MSG_TYPE_TX_CLEANUP",
     "desc": "TX resource cleanup."},
    {"id": 0x13, "name": "HTT_H2T_MSG_TYPE_RX_FETCH",
     "desc": "Requests RX buffers from host to target."},
    {"id": 0x14, "name": "HTT_H2T_MSG_TYPE_RX_FETCH_CONF",
     "desc": "RX buffers received confirmation."},
    {"id": 0x15, "name": "HTT_H2T_MSG_TYPE_RX_OFFLOAD",
     "desc": "Configures RX offloading."},
    {"id": 0x16, "name": "HTT_H2T_MSG_TYPE_PKTLOG_HDR",
     "desc": "Packet logging header."},
    {"id": 0x17, "name": "HTT_H2T_MSG_TYPE_WDS_EXT_MAC",
     "desc": "Extended MAC WDS configuration."},
    {"id": 0x18, "name": "HTT_H2T_MSG_TYPE_TX_COMP_CONF",
     "desc": "TX completion configuration."},
    {"id": 0x19, "name": "HTT_H2T_MSG_TYPE_PEER_MAP",
     "desc": "Peer mapping (station-id -> peer association)."},
    {"id": 0x1A, "name": "HTT_H2T_MSG_TYPE_PEER_UNMAP",
     "desc": "Peer unmap."},
    {"id": 0x1B, "name": "HTT_H2T_MSG_TYPE_MGMT_TX_DESC",
     "desc": "TX management frame descriptor."},
    {"id": 0x1C, "name": "HTT_H2T_MSG_TYPE_SEC_IND",
     "desc": "Security indication (encryption/authentication)."},
    {"id": 0x1D, "name": "HTT_H2T_MSG_TYPE_SMART_LOG_HDR",
     "desc": "Smart logging header."},
    {"id": 0x1E, "name": "HTT_H2T_MSG_TYPE_SRNG_SETUP",
     "desc": "SRNG (Scheduler Ring) configuration."},
    {"id": 0x1F, "name": "HTT_H2T_MSG_TYPE_TYPED_CFG",
     "desc": "Typed configuration (generic parameter)."},
    {"id": 0x20, "name": "HTT_H2T_MSG_TYPE_FLOW_POOL_EXT_CFG",
     "desc": "Extended flow pool configuration."},
    {"id": 0x21, "name": "HTT_H2T_MSG_TYPE_SEC_CFG_V2",
     "desc": "Security configuration version 2."},
    {"id": 0x22, "name": "HTT_H2T_MSG_TYPE_RX_FRM_DEFRAG_CFG",
     "desc": "RX defragmentation configuration."},
    {"id": 0x23, "name": "HTT_H2T_MSG_TYPE_PKTLOG_REGISTER",
     "desc": "Packet logging filter registration."},
    {"id": 0x24, "name": "HTT_H2T_MSG_TYPE_TX_COMP_UNMAP_CFG",
     "desc": "TX completion unmap configuration."},
    {"id": 0x25, "name": "HTT_H2T_MSG_TYPE_PEER_STATS_REQ",
     "desc": "Per-peer statistics request."},
    {"id": 0x26, "name": "HTT_H2T_MSG_TYPE_RX_MONITOR_CFG",
     "desc": "RX monitor configuration."},
    {"id": 0x27, "name": "HTT_H2T_MSG_TYPE_RX_MONITOR_PPDU_DESC_CFG",
     "desc": "PPDU descriptor configuration for RX monitor."},
    {"id": 0x28, "name": "HTT_H2T_MSG_TYPE_PPDU_STATS_REQ",
     "desc": "PPDU statistics request."},
    {"id": 0x29, "name": "HTT_H2T_MSG_TYPE_MAC_OFFLOAD_CFG",
     "desc": "MAC offloading configuration."},
    {"id": 0x2A, "name": "HTT_H2T_MSG_TYPE_WBM2SW_RING_CFG",
     "desc": "WBM-to-SW ring configuration."},
]

# ── T2H table (Target -> Host): 64 messages (0x00-0x3f) ────────────────────

_T2H_MESSAGES: List[Dict[str, Any]] = [
    {"id": 0x00, "name": "HTT_T2H_MSG_TYPE_VERSION_CONF",
     "desc": "HTT version confirmation. Response to VERSION_REQ."},
    {"id": 0x01, "name": "HTT_T2H_MSG_TYPE_RX_FRAG_IND",
     "desc": "RX fragment received indication."},
    {"id": 0x02, "name": "HTT_T2H_MSG_TYPE_FW_STATS_CONF",
     "desc": "Firmware statistics confirmation."},
    {"id": 0x03, "name": "HTT_T2H_MSG_TYPE_TX_COMP_IND",
     "desc": "TX transmission completion indication."},
    {"id": 0x04, "name": "HTT_T2H_MSG_TYPE_TX_SCHED_IND",
     "desc": "TX scheduling indication."},
    {"id": 0x05, "name": "HTT_T2H_MSG_TYPE_PEER_MAP_IND",
     "desc": "Peer mapping completed indication."},
    {"id": 0x06, "name": "HTT_T2H_MSG_TYPE_PEER_UNMAP_IND",
     "desc": "Peer unmap completion indication."},
    {"id": 0x07, "name": "HTT_T2H_MSG_TYPE_RX_OFFLOAD_DELIVER_IND",
     "desc": "RX offloading delivery indication."},
    {"id": 0x08, "name": "HTT_T2H_MSG_TYPE_RX_OFFLOAD_PKTLOSS",
     "desc": "RX offloading packet loss notification."},
    {"id": 0x09, "name": "HTT_T2H_MSG_TYPE_STATS_CONF",
     "desc": "Statistics confirmation."},
    {"id": 0x0A, "name": "HTT_T2H_MSG_TYPE_TX_FETCH_IND",
     "desc": "TX fetch indication from target."},
    {"id": 0x0B, "name": "HTT_T2H_MSG_TYPE_WDI_IPA_OP_RESPONSE",
     "desc": "IPA WDI operation response."},
    {"id": 0x0C, "name": "HTT_T2H_MSG_TYPE_WDI_IPA_CHUNK_READY",
     "desc": "IPA WDI chunk ready."},
    {"id": 0x0D, "name": "HTT_T2H_MSG_TYPE_SMART_LOG_EVENT",
     "desc": "Smart logging event."},
    {"id": 0x0E, "name": "HTT_T2H_MSG_TYPE_TX_CREDIT_UPDATE_IND",
     "desc": "TX credit update (flow control)."},
    {"id": 0x0F, "name": "HTT_T2H_MSG_TYPE_RX_PEER_MAP_IND",
     "desc": "RX peer mapping indication."},
    {"id": 0x10, "name": "HTT_T2H_MSG_TYPE_WDS_EXT_MAC_IND",
     "desc": "Extended MAC WDS indication."},
    {"id": 0x11, "name": "HTT_T2H_MSG_TYPE_PEER_STATS_IND",
     "desc": "Peer statistics."},
    {"id": 0x12, "name": "HTT_T2H_MSG_TYPE_PPDU_STATS_IND",
     "desc": "PPDU statistics."},
    {"id": 0x13, "name": "HTT_T2H_MSG_TYPE_PPDU_DESC_IND",
     "desc": "PPDU descriptor."},
    {"id": 0x14, "name": "HTT_T2H_MSG_TYPE_EMPTY_BUF_IND",
     "desc": "Empty buffer indication."},
    {"id": 0x15, "name": "HTT_T2H_MSG_TYPE_SEC_IND",
     "desc": "Security indication (T2H)."},
    {"id": 0x16, "name": "HTT_T2H_MSG_TYPE_TX_L2_PEER_MAP_IND",
     "desc": "TX peer L2 mapping indication."},
    {"id": 0x17, "name": "HTT_T2H_MSG_TYPE_TX_HW_ENQ_IND",
     "desc": "TX hardware enqueue indication."},
    {"id": 0x18, "name": "HTT_T2H_MSG_TYPE_TX_FLUSH_IND",
     "desc": "TX flush completed indication."},
    {"id": 0x19, "name": "HTT_T2H_MSG_TYPE_PEER_EXT_STATS_IND",
     "desc": "Extended peer statistics."},
    {"id": 0x1A, "name": "HTT_T2H_MSG_TYPE_MAX_LINK_STATS_IND",
     "desc": "Maximum link statistics."},
    {"id": 0x1B, "name": "HTT_T2H_MSG_TYPE_EXT_STATS_CONF",
     "desc": "Extended statistics confirmation."},
    {"id": 0x1C, "name": "HTT_T2H_MSG_TYPE_BSS_CHAN_INFO_RESPONSE",
     "desc": "BSS channel information response."},
    {"id": 0x1D, "name": "HTT_T2H_MSG_TYPE_BEACON_REPORT",
     "desc": "Beacon report."},
    {"id": 0x1E, "name": "HTT_T2H_MSG_TYPE_ERROR_RESPONSE",
     "desc": "Generic error response."},
    {"id": 0x1F, "name": "HTT_T2H_MSG_TYPE_PEER_INFO_IND",
     "desc": "Peer information."},
    {"id": 0x20, "name": "HTT_T2H_MSG_TYPE_MAC_OFFLOAD_IND",
     "desc": "MAC offloading indication."},
    {"id": 0x21, "name": "HTT_T2H_MSG_TYPE_TX_MULTI_PEER_MAP_IND",
     "desc": "TX multi-peer mapping."},
    {"id": 0x22, "name": "HTT_T2H_MSG_TYPE_RX_RING_ERR_IND",
     "desc": "RX ring error."},
    {"id": 0x23, "name": "HTT_T2H_MSG_TYPE_RX_PPDU_START_IND",
     "desc": "RX PPDU start."},
    {"id": 0x24, "name": "HTT_T2H_MSG_TYPE_RX_PPDU_END_IND",
     "desc": "RX PPDU end."},
    {"id": 0x25, "name": "HTT_T2H_MSG_TYPE_TX_OFFLOAD_DELIVER_IND",
     "desc": "TX offloading delivery (fastpath CE)."},
    {"id": 0x26, "name": "HTT_T2H_MSG_TYPE_UPDATE_RX_REO",
     "desc": "RX REO (Re-order) update."},
    {"id": 0x27, "name": "HTT_T2H_MSG_TYPE_TX_TEMPLATE_DESC_ALLOC",
     "desc": "TX template descriptor allocation."},
    {"id": 0x28, "name": "HTT_T2H_MSG_TYPE_TX_DE_ALLOC_IND",
     "desc": "TX de-allocation indication."},
    {"id": 0x29, "name": "HTT_T2H_MSG_TYPE_STATS_DUMP_CMD",
     "desc": "Statistics dump command."},
    {"id": 0x2A, "name": "HTT_T2H_MSG_TYPE_PEER_INFO_EXT_IND",
     "desc": "Extended peer information."},
    {"id": 0x2B, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_PPDU_STATUS",
     "desc": "RX monitor PPDU status."},
    {"id": 0x2C, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_DEST_RING",
     "desc": "RX monitor destination ring."},
    {"id": 0x2D, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_BUFFER",
     "desc": "RX monitor buffer."},
    {"id": 0x2E, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_STATUS_SUMMARY",
     "desc": "RX monitor status summary."},
    {"id": 0x2F, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_PPDU_DESC",
     "desc": "RX monitor PPDU descriptor."},
    {"id": 0x30, "name": "HTT_T2H_MSG_TYPE_TX_MULTI_PEER_MAP_CFM",
     "desc": "TX multi-peer mapping confirmation."},
    {"id": 0x31, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_DEST_RING_CFG",
     "desc": "RX monitor destination ring configuration."},
    {"id": 0x32, "name": "HTT_T2H_MSG_TYPE_6G_LNA_CHAIN_IND",
     "desc": "LNA chain indication for 6 GHz."},
    {"id": 0x33, "name": "HTT_T2H_MSG_TYPE_MAC_OFFLOAD_STATS",
     "desc": "MAC offloading statistics."},
    {"id": 0x34, "name": "HTT_T2H_MSG_TYPE_ATS_IND",
     "desc": "ATS (Accurate Time Service) indication."},
    {"id": 0x35, "name": "HTT_T2H_MSG_TYPE_CFR_IND",
     "desc": "CFR (Channel Frequency Response) indication."},
    {"id": 0x36, "name": "HTT_T2H_MSG_TYPE_CFR_DUMP_CONF",
     "desc": "CFR dump confirmation."},
    {"id": 0x37, "name": "HTT_T2H_MSG_TYPE_MSDUQ_STATS_IND",
     "desc": "MSDU queue statistics."},
    {"id": 0x38, "name": "HTT_T2H_MSG_TYPE_SENSING_STATS_IND",
     "desc": "Sensing statistics."},
    {"id": 0x39, "name": "HTT_T2H_MSG_TYPE_PEER_URGENT_STATS_IND",
     "desc": "Urgent peer statistics."},
    {"id": 0x3A, "name": "HTT_T2H_MSG_TYPE_TX_HWQ_CFG_IND",
     "desc": "TX hardware queue configuration."},
    {"id": 0x3B, "name": "HTT_T2H_MSG_TYPE_WRDA_CMD_IND",
     "desc": "WRDA (Wireless Radio Device Abstraction) command."},
    {"id": 0x3C, "name": "HTT_T2H_MSG_TYPE_WRDA_NON_WLAN_ID_IND",
     "desc": "WRDA non-WLAN identifier."},
    {"id": 0x3D, "name": "HTT_T2H_MSG_TYPE_MAC_PHY_CONFIG_IND",
     "desc": "MAC/PHY configuration."},
    {"id": 0x3E, "name": "HTT_T2H_MSG_TYPE_MLO_CAPS_IND",
     "desc": "MLO (Multi-Link Operation) capabilities."},
    {"id": 0x3F, "name": "HTT_T2H_MSG_TYPE_TX_CREDIT_UPDATE_IND",
     "desc": "TX credit update (last known ID)."},
]

# ── HTT handshake: init sequence ──────────────────────────────────────

_HANDSHAKE_SEQUENCE = [
    {"step": 1, "msg": "VERSION_REQ",
     "direction": "H2T",
     "desc": "Host requests HTT protocol version from target."},
    {"step": 2, "msg": "VERSION_CONF",
     "direction": "T2H",
     "desc": "Target responds with its supported version."},
    {"step": 3, "msg": "FRAG_DESC_BANK_CFG",
     "direction": "H2T",
     "desc": "Host configures fragment descriptor banks."},
    {"step": 4, "msg": "RX_RING_CFG",
     "direction": "H2T",
     "desc": "Host configures DMA receive rings."},
    {"step": 5, "msg": "SRNG_SETUP",
     "direction": "H2T",
     "desc": "Host configures Scheduler Rings."},
    {"step": 6, "msg": "RX_FETCH",
     "direction": "H2T",
     "desc": "Host requests initial RX buffers."},
]

# ── Quick lookup maps ─────────────────────────────────────────────────

_H2T_BY_ID: Dict[int, Dict[str, Any]] = {m["id"]: m for m in _H2T_MESSAGES}
_T2H_BY_ID: Dict[int, Dict[str, Any]] = {m["id"]: m for m in _T2H_MESSAGES}


# ── Public API ────────────────────────────────────────────────────────────

def lookup_htt_message(msg_id: int, direction: str) -> Dict[str, Any]:
    """Look up an HTT message by its numeric ID and direction.

    Args:
        msg_id: Message ID (0-0x2a for H2T, 0-0x3f for T2H).
        direction: "H2T" (Host -> Target) or "T2H" (Target -> Host).

    Returns:
        Dictionary with id, name, desc of the message.

    Raises:
        HTTMessageNotFound: if the ID is outside the known range.
    """
    table = _resolve_table(direction)
    msg = table.get(msg_id)
    if msg is None:
        raise HTTMessageNotFound(
            f"HTT {direction} message ID 0x{msg_id:02X} not found "
            f"(valid range: 0x00-0x{max(table):02X})"
        )
    return dict(msg)


def list_htt_messages(direction: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all known HTT messages.

    Args:
        direction: Optional. "H2T", "T2H", or None (all).

    Returns:
        List of dictionaries with id, name, desc.
    """
    if direction is None:
        result = list(_H2T_MESSAGES) + list(_T2H_MESSAGES)
    else:
        table = _resolve_table(direction)
        result = list(table.values())
    return [dict(m) for m in result]


def get_htt_handshake() -> List[Dict[str, Any]]:
    """Return the complete HTT initialization handshake sequence.

    Returns:
        Ordered list of handshake steps.
    """
    return [dict(step) for step in _HANDSHAKE_SEQUENCE]


# ── Internal helpers ──────────────────────────────────────────────────────

def _resolve_table(direction: str) -> Dict[int, Dict[str, Any]]:
    if direction == "H2T":
        return _H2T_BY_ID
    elif direction == "T2H":
        return _T2H_BY_ID
    else:
        raise ValueError(f"Invalid direction: '{direction}'. Use 'H2T' or 'T2H'.")
