#!/usr/bin/env python3
"""LibrePhone tools — análisis de blobs, protocolos y dependencias.

Módulos:
    htt_protocol       — Lookup de mensajes HTT (Host-Target Transport) de ath11k/WCN6750
    dependency_tracer  — Trazado de dependencias entre blobs WPSS y sus fuentes
    tlv_decoder        — Decodificador de tags TLV del fw-api de WCN6750 (>400 tags)
    mbn_parser         — Parser de archivos MBN/MDT (formato PIL Qualcomm)
"""

from __future__ import annotations

__version__ = "0.1.0"
