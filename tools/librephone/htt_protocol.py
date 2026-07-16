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

"""Lookup de mensajes del protocolo HTT (Host-Target Transport).

Protocolo usado en ath11k/WCN6750 para comunicación host ↔ firmware WPSS.
Datos extraídos del documento técnico `docs/htt.md` (rama `docs/htt-protocol`).

Uso:
    from tools.librephone.htt_protocol import lookup_htt_message, list_htt_messages

    msg = lookup_htt_message(0x00, "H2T")
    print(msg["name"])  # HTT_H2T_MSG_TYPE_VERSION_REQ

    todos = list_htt_messages("H2T")
    print(f"{len(todos)} mensajes H2T conocidos")
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = [
    "HTTMessageNotFound",
    "lookup_htt_message",
    "list_htt_messages",
    "get_htt_handshake",
]


class HTTMessageNotFound(LookupError):
    """El ID de mensaje HTT solicitado no está en el rango conocido."""


# ── Tabla H2T (Host → Target): 43 mensajes (0x00–0x2a) ────────────────────

_H2T_MESSAGES: List[Dict[str, Any]] = [
    {"id": 0x00, "name": "HTT_H2T_MSG_TYPE_VERSION_REQ",
     "desc": "Solicitud de versión del protocolo HTT. Inicia el handshake."},
    {"id": 0x01, "name": "HTT_H2T_MSG_TYPE_FRAG_DESC_BANK_CFG",
     "desc": "Configura bancos de descriptores de fragmentos para RX."},
    {"id": 0x02, "name": "HTT_H2T_MSG_TYPE_RX_RING_CFG",
     "desc": "Configura anillos DMA de recepción (RX rings)."},
    {"id": 0x03, "name": "HTT_H2T_MSG_TYPE_IPA_CFG",
     "desc": "Configura la interfaz IPA (IP Accelerator)."},
    {"id": 0x04, "name": "HTT_H2T_MSG_TYPE_IPA_OFFLOAD_CFG",
     "desc": "Configura offloading IPA."},
    {"id": 0x05, "name": "HTT_H2T_MSG_TYPE_6G_LNA_CHAIN",
     "desc": "Selecciona cadena LNA para banda de 6 GHz."},
    {"id": 0x06, "name": "HTT_H2T_MSG_TYPE_FW_STATS_REQ",
     "desc": "Solicitud de estadísticas del firmware."},
    {"id": 0x07, "name": "HTT_H2T_MSG_TYPE_GET_FW_STATS",
     "desc": "Obtiene estadísticas detalladas del firmware."},
    {"id": 0x08, "name": "HTT_H2T_MSG_TYPE_TX_FETCH_REQ",
     "desc": "Solicita descriptores TX desde el host al target."},
    {"id": 0x09, "name": "HTT_H2T_MSG_TYPE_TX_FETCH_IND",
     "desc": "Indicación de descriptores TX listos."},
    {"id": 0x0A, "name": "HTT_H2T_MSG_TYPE_TX_FETCH_CONF",
     "desc": "Confirmación de descriptores TX recibidos."},
    {"id": 0x0B, "name": "HTT_H2T_MSG_TYPE_TX_FRAG",
     "desc": "Transfiere fragmentos de trama TX."},
    {"id": 0x0C, "name": "HTT_H2T_MSG_TYPE_TX_FRAG_DESC",
     "desc": "Descriptor de fragmento TX."},
    {"id": 0x0D, "name": "HTT_H2T_MSG_TYPE_TX_OFFLOAD",
     "desc": "Solicitud de offloading TX."},
    {"id": 0x0E, "name": "HTT_H2T_MSG_TYPE_TX_OFFLOAD_NORES",
     "desc": "Offloading TX sin recurso adicional."},
    {"id": 0x0F, "name": "HTT_H2T_MSG_TYPE_TX_FLOW_DELETE",
     "desc": "Elimina un flujo TX."},
    {"id": 0x10, "name": "HTT_H2T_MSG_TYPE_TX_FLOW_DELETE_NO_RBM",
     "desc": "Elimina un flujo TX sin retorno de buffer."},
    {"id": 0x11, "name": "HTT_H2T_MSG_TYPE_TX_FLOW_MGMT",
     "desc": "Gestión de flujos TX (creación/modificación)."},
    {"id": 0x12, "name": "HTT_H2T_MSG_TYPE_TX_CLEANUP",
     "desc": "Limpieza de recursos TX."},
    {"id": 0x13, "name": "HTT_H2T_MSG_TYPE_RX_FETCH",
     "desc": "Solicita buffers RX del host al target."},
    {"id": 0x14, "name": "HTT_H2T_MSG_TYPE_RX_FETCH_CONF",
     "desc": "Confirmación de buffers RX recibidos."},
    {"id": 0x15, "name": "HTT_H2T_MSG_TYPE_RX_OFFLOAD",
     "desc": "Configura offloading RX."},
    {"id": 0x16, "name": "HTT_H2T_MSG_TYPE_PKTLOG_HDR",
     "desc": "Cabecera de paquete de logging."},
    {"id": 0x17, "name": "HTT_H2T_MSG_TYPE_WDS_EXT_MAC",
     "desc": "Configuración WDS de MAC extendida."},
    {"id": 0x18, "name": "HTT_H2T_MSG_TYPE_TX_COMP_CONF",
     "desc": "Configuración de completado TX."},
    {"id": 0x19, "name": "HTT_H2T_MSG_TYPE_PEER_MAP",
     "desc": "Mapeo de peer (asociación station-id → peer)."},
    {"id": 0x1A, "name": "HTT_H2T_MSG_TYPE_PEER_UNMAP",
     "desc": "Desmapeo de peer."},
    {"id": 0x1B, "name": "HTT_H2T_MSG_TYPE_MGMT_TX_DESC",
     "desc": "Descriptor para tramas de gestión TX."},
    {"id": 0x1C, "name": "HTT_H2T_MSG_TYPE_SEC_IND",
     "desc": "Indicación de seguridad (cifrado/autenticación)."},
    {"id": 0x1D, "name": "HTT_H2T_MSG_TYPE_SMART_LOG_HDR",
     "desc": "Cabecera de smart logging."},
    {"id": 0x1E, "name": "HTT_H2T_MSG_TYPE_SRNG_SETUP",
     "desc": "Configuración de SRNG (Scheduler Ring)."},
    {"id": 0x1F, "name": "HTT_H2T_MSG_TYPE_TYPED_CFG",
     "desc": "Configuración tipada (parámetro genérico)."},
    {"id": 0x20, "name": "HTT_H2T_MSG_TYPE_FLOW_POOL_EXT_CFG",
     "desc": "Configuración extendida de pool de flujos."},
    {"id": 0x21, "name": "HTT_H2T_MSG_TYPE_SEC_CFG_V2",
     "desc": "Configuración de seguridad versión 2."},
    {"id": 0x22, "name": "HTT_H2T_MSG_TYPE_RX_FRM_DEFRAG_CFG",
     "desc": "Configuración de desfragmentación RX."},
    {"id": 0x23, "name": "HTT_H2T_MSG_TYPE_PKTLOG_REGISTER",
     "desc": "Registro de filtros de packet logging."},
    {"id": 0x24, "name": "HTT_H2T_MSG_TYPE_TX_COMP_UNMAP_CFG",
     "desc": "Configuración de unmap en completado TX."},
    {"id": 0x25, "name": "HTT_H2T_MSG_TYPE_PEER_STATS_REQ",
     "desc": "Solicitud de estadísticas por peer."},
    {"id": 0x26, "name": "HTT_H2T_MSG_TYPE_RX_MONITOR_CFG",
     "desc": "Configuración de monitor RX."},
    {"id": 0x27, "name": "HTT_H2T_MSG_TYPE_RX_MONITOR_PPDU_DESC_CFG",
     "desc": "Configuración de descriptores PPDU para monitor RX."},
    {"id": 0x28, "name": "HTT_H2T_MSG_TYPE_PPDU_STATS_REQ",
     "desc": "Solicitud de estadísticas PPDU."},
    {"id": 0x29, "name": "HTT_H2T_MSG_TYPE_MAC_OFFLOAD_CFG",
     "desc": "Configuración de offloading MAC."},
    {"id": 0x2A, "name": "HTT_H2T_MSG_TYPE_WBM2SW_RING_CFG",
     "desc": "Configuración del anillo WBM-to-SW."},
]

# ── Tabla T2H (Target → Host): 64 mensajes (0x00–0x3f) ────────────────────

_T2H_MESSAGES: List[Dict[str, Any]] = [
    {"id": 0x00, "name": "HTT_T2H_MSG_TYPE_VERSION_CONF",
     "desc": "Confirmación de versión HTT. Respuesta a VERSION_REQ."},
    {"id": 0x01, "name": "HTT_T2H_MSG_TYPE_RX_FRAG_IND",
     "desc": "Indicación de fragmento RX recibido."},
    {"id": 0x02, "name": "HTT_T2H_MSG_TYPE_FW_STATS_CONF",
     "desc": "Confirmación con estadísticas del firmware."},
    {"id": 0x03, "name": "HTT_T2H_MSG_TYPE_TX_COMP_IND",
     "desc": "Indicación de completado de transmisión TX."},
    {"id": 0x04, "name": "HTT_T2H_MSG_TYPE_TX_SCHED_IND",
     "desc": "Indicación de programación TX."},
    {"id": 0x05, "name": "HTT_T2H_MSG_TYPE_PEER_MAP_IND",
     "desc": "Indicación de mapeo de peer completado."},
    {"id": 0x06, "name": "HTT_T2H_MSG_TYPE_PEER_UNMAP_IND",
     "desc": "Indicación de desmapeo de peer completado."},
    {"id": 0x07, "name": "HTT_T2H_MSG_TYPE_RX_OFFLOAD_DELIVER_IND",
     "desc": "Indicación de entrega de offloading RX."},
    {"id": 0x08, "name": "HTT_T2H_MSG_TYPE_RX_OFFLOAD_PKTLOSS",
     "desc": "Notificación de pérdida de paquetes en offloading RX."},
    {"id": 0x09, "name": "HTT_T2H_MSG_TYPE_STATS_CONF",
     "desc": "Confirmación de estadísticas."},
    {"id": 0x0A, "name": "HTT_T2H_MSG_TYPE_TX_FETCH_IND",
     "desc": "Indicación de fetch TX desde target."},
    {"id": 0x0B, "name": "HTT_T2H_MSG_TYPE_WDI_IPA_OP_RESPONSE",
     "desc": "Respuesta de operación IPA WDI."},
    {"id": 0x0C, "name": "HTT_T2H_MSG_TYPE_WDI_IPA_CHUNK_READY",
     "desc": "Chunk IPA WDI listo."},
    {"id": 0x0D, "name": "HTT_T2H_MSG_TYPE_SMART_LOG_EVENT",
     "desc": "Evento de smart logging."},
    {"id": 0x0E, "name": "HTT_T2H_MSG_TYPE_TX_CREDIT_UPDATE_IND",
     "desc": "Actualización de créditos TX (control de flujo)."},
    {"id": 0x0F, "name": "HTT_T2H_MSG_TYPE_RX_PEER_MAP_IND",
     "desc": "Indicación de mapeo de peer RX."},
    {"id": 0x10, "name": "HTT_T2H_MSG_TYPE_WDS_EXT_MAC_IND",
     "desc": "Indicación WDS de MAC extendida."},
    {"id": 0x11, "name": "HTT_T2H_MSG_TYPE_PEER_STATS_IND",
     "desc": "Estadísticas de peer."},
    {"id": 0x12, "name": "HTT_T2H_MSG_TYPE_PPDU_STATS_IND",
     "desc": "Estadísticas PPDU."},
    {"id": 0x13, "name": "HTT_T2H_MSG_TYPE_PPDU_DESC_IND",
     "desc": "Descriptor PPDU."},
    {"id": 0x14, "name": "HTT_T2H_MSG_TYPE_EMPTY_BUF_IND",
     "desc": "Indicación de buffer vacío."},
    {"id": 0x15, "name": "HTT_T2H_MSG_TYPE_SEC_IND",
     "desc": "Indicación de seguridad (T2H)."},
    {"id": 0x16, "name": "HTT_T2H_MSG_TYPE_TX_L2_PEER_MAP_IND",
     "desc": "Indicación de mapeo L2 de peer TX."},
    {"id": 0x17, "name": "HTT_T2H_MSG_TYPE_TX_HW_ENQ_IND",
     "desc": "Indicación de encolamiento TX por hardware."},
    {"id": 0x18, "name": "HTT_T2H_MSG_TYPE_TX_FLUSH_IND",
     "desc": "Indicación de flush TX completado."},
    {"id": 0x19, "name": "HTT_T2H_MSG_TYPE_PEER_EXT_STATS_IND",
     "desc": "Estadísticas extendidas de peer."},
    {"id": 0x1A, "name": "HTT_T2H_MSG_TYPE_MAX_LINK_STATS_IND",
     "desc": "Estadísticas máximas de enlace."},
    {"id": 0x1B, "name": "HTT_T2H_MSG_TYPE_EXT_STATS_CONF",
     "desc": "Confirmación de estadísticas extendidas."},
    {"id": 0x1C, "name": "HTT_T2H_MSG_TYPE_BSS_CHAN_INFO_RESPONSE",
     "desc": "Respuesta de información de canal BSS."},
    {"id": 0x1D, "name": "HTT_T2H_MSG_TYPE_BEACON_REPORT",
     "desc": "Reporte de beacon."},
    {"id": 0x1E, "name": "HTT_T2H_MSG_TYPE_ERROR_RESPONSE",
     "desc": "Respuesta de error genérica."},
    {"id": 0x1F, "name": "HTT_T2H_MSG_TYPE_PEER_INFO_IND",
     "desc": "Información de peer."},
    {"id": 0x20, "name": "HTT_T2H_MSG_TYPE_MAC_OFFLOAD_IND",
     "desc": "Indicación de offloading MAC."},
    {"id": 0x21, "name": "HTT_T2H_MSG_TYPE_TX_MULTI_PEER_MAP_IND",
     "desc": "Mapeo multi-peer TX."},
    {"id": 0x22, "name": "HTT_T2H_MSG_TYPE_RX_RING_ERR_IND",
     "desc": "Error en anillo RX."},
    {"id": 0x23, "name": "HTT_T2H_MSG_TYPE_RX_PPDU_START_IND",
     "desc": "Inicio de PPDU RX."},
    {"id": 0x24, "name": "HTT_T2H_MSG_TYPE_RX_PPDU_END_IND",
     "desc": "Fin de PPDU RX."},
    {"id": 0x25, "name": "HTT_T2H_MSG_TYPE_TX_OFFLOAD_DELIVER_IND",
     "desc": "Entrega de offloading TX (fastpath CE)."},
    {"id": 0x26, "name": "HTT_T2H_MSG_TYPE_UPDATE_RX_REO",
     "desc": "Actualización de REO (Re-order) RX."},
    {"id": 0x27, "name": "HTT_T2H_MSG_TYPE_TX_TEMPLATE_DESC_ALLOC",
     "desc": "Asignación de descriptor de plantilla TX."},
    {"id": 0x28, "name": "HTT_T2H_MSG_TYPE_TX_DE_ALLOC_IND",
     "desc": "Indicación de desasignación TX."},
    {"id": 0x29, "name": "HTT_T2H_MSG_TYPE_STATS_DUMP_CMD",
     "desc": "Comando de volcado de estadísticas."},
    {"id": 0x2A, "name": "HTT_T2H_MSG_TYPE_PEER_INFO_EXT_IND",
     "desc": "Información extendida de peer."},
    {"id": 0x2B, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_PPDU_STATUS",
     "desc": "Estado de PPDU de monitor RX."},
    {"id": 0x2C, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_DEST_RING",
     "desc": "Anillo destino de monitor RX."},
    {"id": 0x2D, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_BUFFER",
     "desc": "Buffer de monitor RX."},
    {"id": 0x2E, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_STATUS_SUMMARY",
     "desc": "Resumen de estado de monitor RX."},
    {"id": 0x2F, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_PPDU_DESC",
     "desc": "Descriptor PPDU de monitor RX."},
    {"id": 0x30, "name": "HTT_T2H_MSG_TYPE_TX_MULTI_PEER_MAP_CFM",
     "desc": "Confirmación de mapeo multi-peer TX."},
    {"id": 0x31, "name": "HTT_T2H_MSG_TYPE_RX_MONITOR_DEST_RING_CFG",
     "desc": "Configuración de anillo destino de monitor RX."},
    {"id": 0x32, "name": "HTT_T2H_MSG_TYPE_6G_LNA_CHAIN_IND",
     "desc": "Indicación de cadena LNA para 6 GHz."},
    {"id": 0x33, "name": "HTT_T2H_MSG_TYPE_MAC_OFFLOAD_STATS",
     "desc": "Estadísticas de offloading MAC."},
    {"id": 0x34, "name": "HTT_T2H_MSG_TYPE_ATS_IND",
     "desc": "Indicación ATS (Accurate Time Service)."},
    {"id": 0x35, "name": "HTT_T2H_MSG_TYPE_CFR_IND",
     "desc": "Indicación CFR (Channel Frequency Response)."},
    {"id": 0x36, "name": "HTT_T2H_MSG_TYPE_CFR_DUMP_CONF",
     "desc": "Confirmación de dump CFR."},
    {"id": 0x37, "name": "HTT_T2H_MSG_TYPE_MSDUQ_STATS_IND",
     "desc": "Estadísticas de cola MSDU."},
    {"id": 0x38, "name": "HTT_T2H_MSG_TYPE_SENSING_STATS_IND",
     "desc": "Estadísticas de sensing."},
    {"id": 0x39, "name": "HTT_T2H_MSG_TYPE_PEER_URGENT_STATS_IND",
     "desc": "Estadísticas urgentes de peer."},
    {"id": 0x3A, "name": "HTT_T2H_MSG_TYPE_TX_HWQ_CFG_IND",
     "desc": "Configuración de hardware queue TX."},
    {"id": 0x3B, "name": "HTT_T2H_MSG_TYPE_WRDA_CMD_IND",
     "desc": "Comando WRDA (Wireless Radio Device Abstraction)."},
    {"id": 0x3C, "name": "HTT_T2H_MSG_TYPE_WRDA_NON_WLAN_ID_IND",
     "desc": "Identificador non-WLAN WRDA."},
    {"id": 0x3D, "name": "HTT_T2H_MSG_TYPE_MAC_PHY_CONFIG_IND",
     "desc": "Configuración MAC/PHY."},
    {"id": 0x3E, "name": "HTT_T2H_MSG_TYPE_MLO_CAPS_IND",
     "desc": "Capacidades MLO (Multi-Link Operation)."},
    {"id": 0x3F, "name": "HTT_T2H_MSG_TYPE_TX_CREDIT_UPDATE_IND",
     "desc": "Actualización de créditos TX (último ID conocido)."},
]

# ── Handshake HTT: secuencia de init ──────────────────────────────────────

_HANDSHAKE_SEQUENCE = [
    {"step": 1, "msg": "VERSION_REQ",
     "direction": "H2T",
     "desc": "Host solicita versión del protocolo HTT al target."},
    {"step": 2, "msg": "VERSION_CONF",
     "direction": "T2H",
     "desc": "Target responde con su versión soportada."},
    {"step": 3, "msg": "FRAG_DESC_BANK_CFG",
     "direction": "H2T",
     "desc": "Host configura bancos de descriptores de fragmentos."},
    {"step": 4, "msg": "RX_RING_CFG",
     "direction": "H2T",
     "desc": "Host configura anillos DMA de recepción."},
    {"step": 5, "msg": "SRNG_SETUP",
     "direction": "H2T",
     "desc": "Host configura Scheduler Rings."},
    {"step": 6, "msg": "RX_FETCH",
     "direction": "H2T",
     "desc": "Host solicita buffers RX iniciales."},
]

# ── Mapas de lookup rápido ─────────────────────────────────────────────────

_H2T_BY_ID: Dict[int, Dict[str, Any]] = {m["id"]: m for m in _H2T_MESSAGES}
_T2H_BY_ID: Dict[int, Dict[str, Any]] = {m["id"]: m for m in _T2H_MESSAGES}


# ── API pública ────────────────────────────────────────────────────────────

def lookup_htt_message(msg_id: int, direction: str) -> Dict[str, Any]:
    """Busca un mensaje HTT por su ID numérico y dirección.

    Args:
        msg_id: ID del mensaje (0–0x2a para H2T, 0–0x3f para T2H).
        direction: "H2T" (Host → Target) o "T2H" (Target → Host).

    Returns:
        Diccionario con id, name, desc del mensaje.

    Raises:
        HTTMessageNotFound: si el ID está fuera del rango conocido.
    """
    table = _resolve_table(direction)
    msg = table.get(msg_id)
    if msg is None:
        raise HTTMessageNotFound(
            f"Mensaje HTT {direction} ID 0x{msg_id:02X} no encontrado "
            f"(rango válido: 0x00–0x{max(table):02X})"
        )
    return dict(msg)


def list_htt_messages(direction: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todos los mensajes HTT conocidos.

    Args:
        direction: Opcional. "H2T", "T2H" o None (todos).

    Returns:
        Lista de diccionarios con id, name, desc.
    """
    if direction is None:
        result = list(_H2T_MESSAGES) + list(_T2H_MESSAGES)
    else:
        table = _resolve_table(direction)
        result = list(table.values())
    return [dict(m) for m in result]


def get_htt_handshake() -> List[Dict[str, Any]]:
    """Devuelve la secuencia completa del handshake de inicialización HTT.

    Returns:
        Lista ordenada de pasos del handshake.
    """
    return [dict(step) for step in _HANDSHAKE_SEQUENCE]


# ── Helpers internos ───────────────────────────────────────────────────────

def _resolve_table(direction: str) -> Dict[int, Dict[str, Any]]:
    if direction == "H2T":
        return _H2T_BY_ID
    elif direction == "T2H":
        return _T2H_BY_ID
    else:
        raise ValueError(f"Dirección inválida: '{direction}'. Use 'H2T' o 'T2H'.")
