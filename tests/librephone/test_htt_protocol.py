#!/usr/bin/env python3
"""Tests para tools.librephone.htt_protocol."""

from __future__ import annotations

import pytest

from tools.librephone.htt_protocol import (
    HTTMessageNotFound,
    get_htt_handshake,
    list_htt_messages,
    lookup_htt_message,
)


class TestLookupHTTMessage:
    """Tests para lookup_htt_message()."""

    def test_lookup_valid_h2t(self) -> None:
        msg = lookup_htt_message(0x00, "H2T")
        assert msg["name"] == "HTT_H2T_MSG_TYPE_VERSION_REQ"
        assert msg["id"] == 0x00
        assert "desc" in msg

    def test_lookup_valid_t2h(self) -> None:
        msg = lookup_htt_message(0x00, "T2H")
        assert msg["name"] == "HTT_T2H_MSG_TYPE_VERSION_CONF"
        assert msg["id"] == 0x00

    def test_lookup_invalid_id(self) -> None:
        with pytest.raises(HTTMessageNotFound):
            lookup_htt_message(0xFF, "H2T")

    def test_lookup_invalid_direction(self) -> None:
        with pytest.raises(ValueError, match="Invalid direction"):
            lookup_htt_message(0x00, "XXX")  # type: ignore[arg-type]

    def test_lookup_h2t_last(self) -> None:
        msg = lookup_htt_message(0x2A, "H2T")
        assert msg["name"] == "HTT_H2T_MSG_TYPE_WBM2SW_RING_CFG"

    def test_lookup_t2h_last(self) -> None:
        msg = lookup_htt_message(0x3F, "T2H")
        assert "CREDIT_UPDATE" in msg["name"]


class TestListHTTMessages:
    """Tests para list_htt_messages()."""

    def test_list_all_h2t(self) -> None:
        msgs = list_htt_messages("H2T")
        assert len(msgs) == 43

    def test_list_all_t2h(self) -> None:
        msgs = list_htt_messages("T2H")
        assert len(msgs) == 64

    def test_list_all(self) -> None:
        msgs = list_htt_messages(None)
        assert len(msgs) == 43 + 64

    def test_list_invalid_direction(self) -> None:
        with pytest.raises(ValueError, match="Invalid direction"):
            list_htt_messages("BIDI")  # type: ignore[arg-type]

    def test_list_contains_known(self) -> None:
        msgs = list_htt_messages("H2T")
        names = {m["name"] for m in msgs}
        assert "HTT_H2T_MSG_TYPE_VERSION_REQ" in names
        assert "HTT_H2T_MSG_TYPE_RX_RING_CFG" in names
        assert "HTT_H2T_MSG_TYPE_SRNG_SETUP" in names


class TestGetHandshake:
    """Tests para get_htt_handshake()."""

    def test_handshake_length(self) -> None:
        steps = get_htt_handshake()
        assert len(steps) == 6

    def test_handshake_first(self) -> None:
        steps = get_htt_handshake()
        assert steps[0]["msg"] == "VERSION_REQ"
        assert steps[0]["direction"] == "H2T"
        assert steps[0]["step"] == 1

    def test_handshake_last(self) -> None:
        steps = get_htt_handshake()
        assert steps[-1]["msg"] == "RX_FETCH"
        assert steps[-1]["step"] == 6

    def test_handshake_version_conf_present(self) -> None:
        steps = get_htt_handshake()
        msg_names = [s["msg"] for s in steps]
        assert "VERSION_REQ" in msg_names
        assert "VERSION_CONF" in msg_names
        assert "FRAG_DESC_BANK_CFG" in msg_names
        assert "RX_RING_CFG" in msg_names
        assert "SRNG_SETUP" in msg_names
        assert "RX_FETCH" in msg_names
