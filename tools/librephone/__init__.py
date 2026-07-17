#!/usr/bin/env python3
"""LibrePhone tools — blob, protocol, and dependency analysis.

Modules:
    htt_protocol       — HTT (Host-Target Transport) message lookup for ath11k/WCN6750
    dependency_tracer  — WPSS blob dependency tracing and source mapping
    tlv_decoder        — TLV tag decoder for WCN6750 fw-api (>400 tags)
    mbn_parser         — MBN/MDT file parser (Qualcomm PIL format)
"""

from __future__ import annotations

__version__ = "0.1.0"
