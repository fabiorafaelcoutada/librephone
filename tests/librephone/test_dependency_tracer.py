#!/usr/bin/env python3
"""Tests para tools.librephone.dependency_tracer."""

from __future__ import annotations

import pytest

from tools.librephone.dependency_tracer import (
    BlobNotFound,
    estimate_coverage,
    find_blob_source,
    list_known_blobs,
    trace_dependencies,
)


class TestListKnownBlobs:
    def test_list_not_empty(self) -> None:
        blobs = list_known_blobs()
        assert len(blobs) > 0
        assert "wlanmdsp.mbn" in blobs


class TestTraceDependencies:
    """Tests para trace_dependencies()."""

    def test_trace_known_blob(self) -> None:
        deps = trace_dependencies("wlanmdsp.mbn")
        assert deps["blob"] == "wlanmdsp.mbn"
        assert deps["category"] == "firmware_wifi"
        assert deps["status"] == "proprietary"
        assert len(deps["depends_on"]) >= 1
        dep_names = [d["name"] for d in deps["depends_on"]]
        assert "wcnss.mbn" in dep_names
        assert "qdsp6.mbn" in dep_names

    def test_trace_unknown_blob(self) -> None:
        with pytest.raises(BlobNotFound):
            trace_dependencies("blob_que_no_existe.bin")

    def test_trace_leaf_blob(self) -> None:
        """Blob sin dependencias."""
        deps = trace_dependencies("keymaster.mbn")
        assert deps["depends_on"] == []

    def test_trace_desc_and_size(self) -> None:
        deps = trace_dependencies("qdsp6.mbn")
        assert "description" in deps
        assert "size_estimate" in deps


class TestFindBlobSource:
    """Tests para find_blob_source()."""

    def test_find_source_ota_available(self) -> None:
        source = find_blob_source("wcnss.mbn")
        assert source["available_in_ota"] is True
        assert source["location"] is not None
        assert source["method"] is not None

    def test_find_source_ota_unavailable(self) -> None:
        """wlanmdsp.mbn NO está en OTA."""
        source = find_blob_source("wlanmdsp.mbn")
        assert source["available_in_ota"] is False
        assert "ADB pull" in source["method"]

    def test_find_source_local_blobs(self) -> None:
        """Blobs ya extraídos localmente a blobs/fp6/."""
        source = find_blob_source("CAMERA_ICP.mbn")
        assert source["available_in_ota"] is True
        assert "extraído localmente" in source["method"]

    def test_source_unknown_blob(self) -> None:
        with pytest.raises(BlobNotFound):
            find_blob_source("nonexistent.bin")


class TestEstimateCoverage:
    """Tests para estimate_coverage()."""

    def test_coverage_is_dict(self) -> None:
        cov = estimate_coverage()
        assert "total_blobs" in cov
        assert "counts" in cov
        assert "percentages" in cov

    def test_coverage_percentages_sum(self) -> None:
        cov = estimate_coverage()
        total_pct = sum(cov["percentages"].values())
        assert abs(total_pct - 100.0) < 0.5

    def test_coverage_total_positive(self) -> None:
        cov = estimate_coverage()
        assert cov["total_blobs"] > 0

    def test_coverage_counts_match_total(self) -> None:
        cov = estimate_coverage()
        assert sum(cov["counts"].values()) == cov["total_blobs"]
