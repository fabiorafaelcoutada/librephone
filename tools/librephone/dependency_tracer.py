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
    """El blob solicitado no está en la base de conocimiento."""


class SourceUnavailable(ValueError):
    """No se conoce fuente disponible para este blob."""


# ── Base de conocimiento de blobs ─────────────────────────────────────────

_KNOWN_BLOBS: Dict[str, Dict[str, Any]] = {
    "wlanmdsp.mbn": {
        "description": "Firmware WPSS WCN6750. Blob principal del chip WiFi/BT.",
        "depends_on": ["wcnss.mbn", "qdsp6.mbn"],
        "depended_by": ["mcfg.mbn"],
        "source": {
            "location": "/data/vendor/firmware/wlanmdsp.mbn",
            "method": "ADB pull desde FP6 real",
            "available_in_ota": False,
            "notes": "No incluido en OTA LineageOS. Extraer desde dispositivo físico.",
        },
        "status": "propietario",
        "category": "firmware_wifi",
        "size_estimate": "~4-6 MB",
    },
    "wcnss.mbn": {
        "description": "Wireless Connectivity Subsystem. Dependencia del firmware WiFi.",
        "depends_on": ["qdsp6.mbn"],
        "depended_by": ["wlanmdsp.mbn"],
        "source": {
            "location": "/firmware/image/wcnss.mbn",
            "method": "Stock firmware Fairphone o ADB pull",
            "available_in_ota": True,
            "notes": "Disponible en partición firmware de OTA.",
        },
        "status": "propietario",
        "category": "firmware_wifi",
        "size_estimate": "~2-3 MB",
    },
    "qdsp6.mbn": {
        "description": "DSP firmware (Qualcomm Hexagon). Procesamiento de señal digital.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": ["wlanmdsp.mbn", "wcnss.mbn"],
        "source": {
            "location": "/firmware/image/qdsp6.mbn",
            "method": "Stock firmware Fairphone o ADB pull",
            "available_in_ota": True,
            "notes": "Hexagon DSP. Esencial para iniciar WPSS.",
        },
        "status": "propietario",
        "category": "dsp",
        "size_estimate": "~8-12 MB",
    },
    "cmnlib.mbn": {
        "description": "Common Library (TrustZone). Librería compartida del entorno seguro.",
        "depends_on": ["keymaster.mbn"],
        "depended_by": ["qdsp6.mbn"],
        "source": {
            "location": "/firmware/image/cmnlib.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Parte del Secure World. Necesaria para PIL loading.",
        },
        "status": "propietario",
        "category": "trustzone",
        "size_estimate": "~256 KB",
    },
    "keymaster.mbn": {
        "description": "Secure key storage. Gestión de claves criptográficas en TrustZone.",
        "depends_on": [],
        "depended_by": ["cmnlib.mbn"],
        "source": {
            "location": "/firmware/image/keymaster.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Módulo de seguridad de claves.",
        },
        "status": "propietario",
        "category": "trustzone",
        "size_estimate": "~128 KB",
    },
    "venus.mbn": {
        "description": "VPU firmware (Video Processing Unit). Codificación/decodificación video.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": [],
        "source": {
            "location": "/firmware/image/venus.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Firmware de VPU. No relacionado con WiFi.",
        },
        "status": "propietario",
        "category": "multimedia",
        "size_estimate": "~512 KB",
    },
    "mcfg.mbn": {
        "description": "Modem configuration. Configuración de bandas y protocolos celulares.",
        "depends_on": ["qdsp6.mbn"],
        "depended_by": [],
        "source": {
            "location": "/firmware/image/mcfg.mbn",
            "method": "Stock firmware Fairphone",
            "available_in_ota": True,
            "notes": "Configuración del módem celular.",
        },
        "status": "propietario",
        "category": "modem",
        "size_estimate": "~1-2 MB",
    },
    "CAMERA_ICP.mbn": {
        "description": "Firmware de cámara ICP (Image Co-Processor).",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": [],
        "source": {
            "location": "vendor/firmware/ (OTA)",
            "method": "OTA LineageOS FP6 — ya extraído localmente",
            "available_in_ota": True,
            "notes": "Extraído a blobs/fp6/. No relacionado con WiFi.",
        },
        "status": "propietario",
        "category": "camera",
        "size_estimate": "~128 KB",
    },
    "gen70900_zap.mbn": {
        "description": "GPU ZAP shader (Gen 7.9.0). Security blob para inicialización GPU.",
        "depends_on": ["cmnlib.mbn"],
        "depended_by": [],
        "source": {
            "location": "vendor/firmware/ (OTA)",
            "method": "OTA LineageOS FP6 — ya extraído localmente",
            "available_in_ota": True,
            "notes": "Blob de seguridad GPU. Extraído a blobs/fp6/.",
        },
        "status": "propietario",
        "category": "gpu",
        "size_estimate": "~64 KB",
    },
    "wpss.b12": {
        "description": "Certificados Secure Boot WPSS. 3 × X.509 v3 DER concatenados.",
        "depends_on": [],
        "depended_by": ["wlanmdsp.mbn"],
        "source": {
            "location": "wpss.b12 (dentro de wlanmdsp.mbn)",
            "method": "Extracción desde wlanmdsp.mbn (no disponible aún)",
            "available_in_ota": False,
            "notes": "No disponible sin wlanmdsp.mbn. Contiene Root CA, 3 certs.",
        },
        "status": "documentado",
        "category": "secure_boot",
        "size_estimate": "~4 KB",
    },
}

# ── Épocas de análisis ────────────────────────────────────────────────────

_COVERAGE_TIMESTAMP = "2026-07-15"


# ── API pública ────────────────────────────────────────────────────────────

def list_known_blobs() -> List[str]:
    """Lista todos los blobs conocidos en la base de conocimiento.

    Returns:
        Lista de nombres de blob.
    """
    return sorted(_KNOWN_BLOBS.keys())


def trace_dependencies(blob_name: str) -> Dict[str, Any]:
    """Traza el árbol de dependencias de un blob.

    Args:
        blob_name: Nombre del blob (ej. "wlanmdsp.mbn").

    Returns:
        Diccionario con el blob, sus dependencias y dependientes.

    Raises:
        BlobNotFound: si el blob no está en la base de conocimiento.
    """
    blob = _KNOWN_BLOBS.get(blob_name)
    if blob is None:
        raise BlobNotFound(
            f"Blob '{blob_name}' no encontrado. "
            f"Conocidos: {', '.join(list_known_blobs())}"
        )

    # Resolver dependencias recursivas (un nivel)
    resolved_deps = []
    for dep in blob["depends_on"]:
        if dep in _KNOWN_BLOBS:
            resolved_deps.append({
                "name": dep,
                "description": _KNOWN_BLOBS[dep]["description"],
                "status": _KNOWN_BLOBS[dep]["status"],
            })
        else:
            resolved_deps.append({"name": dep, "description": "desconocido", "status": "desconocido"})

    resolved_by = []
    for dep in blob["depended_by"]:
        if dep in _KNOWN_BLOBS:
            resolved_by.append({
                "name": dep,
                "description": _KNOWN_BLOBS[dep]["description"],
                "status": _KNOWN_BLOBS[dep]["status"],
            })
        else:
            resolved_by.append({"name": dep, "description": "desconocido", "status": "desconocido"})

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
    """Encuentra la fuente de obtención recomendada para un blob.

    Args:
        blob_name: Nombre del blob.

    Returns:
        Diccionario con location, method, available_in_ota, notes.

    Raises:
        BlobNotFound: si el blob no está en la base de conocimiento.
    """
    blob = _KNOWN_BLOBS.get(blob_name)
    if blob is None:
        raise BlobNotFound(f"Blob '{blob_name}' no encontrado.")
    return dict(blob["source"])


def estimate_coverage() -> Dict[str, Any]:
    """Estima el porcentaje de documentación y reemplazos libres.

    Clasifica blobs como:
        - propietario: sin documentación pública suficiente
        - documentado: estructura analizada, pero sin reemplazo libre
        - libre: existe o se puede generar reemplazo libre

    Returns:
        Diccionario con total, conteo por status, y porcentajes.
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
