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

"""Dependency tracing between WPSS firmware blobs and their sources.

Analyzes which blobs depend on others, where to obtain them, and estimates
the free vs proprietary coverage percentage.

Usage:
    from tools.librephone.dependency_tracer import trace_dependencies, find_blob_source

    deps = trace_dependencies("wlanmdsp.mbn")
    print(deps["depends_on"])

    source = find_blob_source("wlanmdsp.mbn")
    print(source["method"])
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = [
    "BlobNotFound",
    "SourceUnavailable",
    "trace_dependencies",
    "find_blob_source",
    "estimate_coverage",
    "list_known_blobs",
]


class BlobNotFound(LookupError):
    """The requested blob is not in the knowledge base."""


class SourceUnavailable(ValueError):
    """No known available source for this blob."""


# ── Blob knowledge base ────────────────────────────────────────────

_KNOWN_BLOBS: Dict[str, Dict[str, Any]] = {
    "wlanmdsp.mbn": {
        "description": "WPSS WCN6750 firmware. Main WiFi/BT chip blob.",
        "depends_on": ["wcnss.mbn", "qdsp6.mbn"],
        "depended_by": ["mcfg.mbn"],
        "source": {
            "location": "/data/vendor/firmware/wlanmdsp.mbn",
            "method": "ADB pull desde FP6 real",
            "available_in_ota": False,
            "notes": "Not included in LineageOS OTA. Extract from physical device.",
        },
        "status": "proprietary",
        "category": "firmware_wifi",
        "size_estimate": "~4-6 MB",
    },
    "wcnss.mbn": {
        "description": "Wireless Connectivity Subsystem. WiFi firmware dependency.",
        "depends_on": ["qdsp6.mbn"],
        "depended_by": ["wlanmdsp.mbn"],
        "source": {
            "location": "/firmware/image/wcnss.mbn",
            "method": "Stock firmware Fairphone o ADB pull",
            "available_in_ota": True,
            "notes": "Available in OTA firmware partition.",
        },
        "status": "proprietary",
        "category": "firmware_wifi",
        "size_estimate": "~2-3 MB",
    },
    "qdsp6.mbn": {
        "description": "DSP firmware (Qualcomm Hexagon). Digital signal processing.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": ["wlanmdsp.mbn", "wcnss.mbn"],
        "source": {
            "location": "/firmware/image/qdsp6.mbn",
            "method": "Stock firmware Fairphone o ADB pull",
            "available_in_ota": True,
            "notes": "Hexagon DSP. Essential for WPSS boot.",
        },
        "status": "proprietary",
        "category": "dsp",
        "size_estimate": "~8-12 MB",
    },
    "cmnlib.mbn": {
        "description": "Common Library (TrustZone). Shared library for the secure environment.",
        "depends_on": ["keymaster.mbn"],
        "depended_by": ["qdsp6.mbn"],
        "source": {
            "location": "/firmware/image/cmnlib.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Part of the Secure World. Required for PIL loading.",
        },
        "status": "proprietary",
        "category": "trustzone",
        "size_estimate": "~256 KB",
    },
    "keymaster.mbn": {
        "description": "Secure key storage. Cryptographic key management in TrustZone.",
        "depends_on": [],
        "depended_by": ["cmnlib.mbn"],
        "source": {
            "location": "/firmware/image/keymaster.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Key security module.",
        },
        "status": "proprietary",
        "category": "trustzone",
        "size_estimate": "~128 KB",
    },
    "venus.mbn": {
        "description": "VPU firmware (Video Processing Unit). Video encoding/decoding.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": [],
        "source": {
            "location": "/firmware/image/venus.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "VPU firmware. Not WiFi-related.",
        },
        "status": "proprietary",
        "category": "multimedia",
        "size_estimate": "~512 KB",
    },
    "mcfg.mbn": {
        "description": "Modem configuration. Cellular band and protocol configuration.",
        "depends_on": ["qdsp6.mbn"],
        "depended_by": [],
        "source": {
            "location": "/firmware/image/mcfg.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Cellular modem configuration.",
        },
        "status": "proprietary",
        "category": "modem",
        "size_estimate": "~1-2 MB",
    },
    "CAMERA_ICP.mbn": {
        "description": "ICP (Image Co-Processor) camera firmware.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": [],
        "source": {
            "location": "vendor/firmware/ (OTA)",
            "method": "OTA LineageOS FP6 — ya extraído localmente",
            "available_in_ota": True,
            "notes": "Extracted to blobs/fp6/. Not WiFi-related.",
        },
        "status": "proprietary",
        "category": "camera",
        "size_estimate": "~128 KB",
    },
    "gen70900_zap.mbn": {
        "description": "GPU ZAP shader (Gen 7.9.0). Security blob for GPU initialization.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": [],
        "source": {
            "location": "vendor/firmware/ (OTA)",
            "method": "OTA LineageOS FP6 — ya extraído localmente",
            "available_in_ota": True,
            "notes": "GPU security blob. Extracted to blobs/fp6/.",
        },
        "status": "proprietary",
        "category": "gpu",
        "size_estimate": "~64 KB",
    },
    "wpss.b12": {
        "description": "WPSS Secure Boot certificates. 3 × X.509 v3 DER concatenated.",
        "depends_on": [],
        "depended_by": ["wlanmdsp.mbn"],
        "source": {
            "location": "wpss.b12 (inside wlanmdsp.mbn)",
            "method": "Extraction from wlanmdsp.mbn (not yet available)",
            "available_in_ota": False,
            "notes": "Not available without wlanmdsp.mbn. Contains Root CA, 3 certs.",
        },
        "status": "documented",
        "category": "secure_boot",
        "size_estimate": "~4 KB",
    },
}

# ── Analysis epochs ──────────────────────────────────────────────────────

_COVERAGE_TIMESTAMP = "2026-07-15"


# ── Public API ────────────────────────────────────────────────────────────

def list_known_blobs() -> List[str]:
    """List all known blobs in the knowledge base.

    Returns:
        List of blob names.
    """
    return sorted(_KNOWN_BLOBS.keys())


def trace_dependencies(blob_name: str) -> Dict[str, Any]:
    """Trace the dependency tree of a blob.

    Args:
        blob_name: Blob name (e.g. "wlanmdsp.mbn").

    Returns:
        Dictionary with blob, its dependencies, and dependents.

    Raises:
        BlobNotFound: if the blob is not in the knowledge base.
    """
    blob = _KNOWN_BLOBS.get(blob_name)
    if blob is None:
        raise BlobNotFound(
            f"Blob '{blob_name}' not found. "
            f"Known: {', '.join(list_known_blobs())}"
        )

    # Resolve recursive dependencies (one level)
    resolved_deps = []
    for dep in blob["depends_on"]:
        if dep in _KNOWN_BLOBS:
            resolved_deps.append({
                "name": dep,
                "description": _KNOWN_BLOBS[dep]["description"],
                "status": _KNOWN_BLOBS[dep]["status"],
            })
        else:
            resolved_deps.append({"name": dep, "description": "unknown", "status": "unknown"})

    resolved_by = []
    for dep in blob["depended_by"]:
        if dep in _KNOWN_BLOBS:
            resolved_by.append({
                "name": dep,
                "description": _KNOWN_BLOBS[dep]["description"],
                "status": _KNOWN_BLOBS[dep]["status"],
            })
        else:
            resolved_by.append({"name": dep, "description": "unknown", "status": "unknown"})

    return {
        "blob": blob_name,
        "description": blob["description"],
        "category": blob["category"],
        "status": blob["status"],
        "size_estimate": blob["size_estimate"],
        "depends_on": resolved_deps,
        "depended_by": resolved_by,
    }


def find_blob_source(blob_name: str) -> Dict[str, Any]:
    """Find the recommended source for obtaining a blob.

    Args:
        blob_name: Blob name.

    Returns:
        Dictionary with location, method, available_in_ota, notes.

    Raises:
        BlobNotFound: if the blob is not in the knowledge base.
    """
    blob = _KNOWN_BLOBS.get(blob_name)
    if blob is None:
        raise BlobNotFound(f"Blob '{blob_name}' not found.")
    return dict(blob["source"])


def estimate_coverage() -> Dict[str, Any]:
    """Estimate documentation and free replacement coverage percentage.

    Classifies blobs as:
        - proprietary: insufficient public documentation
        - documented: structure analyzed, but no free replacement
        - free: free replacement exists or can be generated

    Returns:
        Dictionary with total, count by status, and percentages.
    """
    total = len(_KNOWN_BLOBS)
    counts: Dict[str, int] = {}
    for blob in _KNOWN_BLOBS.values():
        s = blob["status"]
        counts[s] = counts.get(s, 0) + 1

    coverage = {
        "total_blobs": total,
        "counts": dict(counts),
        "percentages": {
            s: round(c / total * 100, 1) for s, c in counts.items()
        },
        "timestamp": _COVERAGE_TIMESTAMP,
        "note": "Solo blobs WPSS/FP6 conocidos. No incluye módem, sensor u otros subsistemas.",
    }
    return coverage
