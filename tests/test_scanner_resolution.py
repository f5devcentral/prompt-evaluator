# Copyright 2025 Andy Ryan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python3
"""Tests for scanner ID to name resolution in prompt_evaluator.

Covers the triggered-scanner reporting feature: building the scanner map from
the paged /scanners endpoint, resolving scanner IDs on individual scans, and
serialising the resulting list into the flat output formats.
"""

import csv
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# The module reads credentials at import time, so provide throwaway values
# before importing it. No network calls are made by the import itself.
os.environ.setdefault("CALYPSOAI_URL", "https://calypsoai.test")
os.environ.setdefault("CALYPSOAI_TOKEN", "test_token_12345")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import prompt_evaluator as pe  # noqa: E402


@pytest.fixture(autouse=True)
def reset_scanner_cache():
    """Clear the module-level scanner map cache around every test."""
    pe._scanner_map_cache = None
    yield
    pe._scanner_map_cache = None


def _mock_session(payload_by_source, failing_sources=()):
    """Build a mock requests.Session whose GET returns per-source payloads.

    Args:
        payload_by_source: {source_name: json payload} returned by the API.
        failing_sources: Sources that should raise a RequestException.

    Returns:
        A MagicMock usable as a context manager in place of requests.Session().
    """
    session = MagicMock()

    def _get(url, params=None, timeout=None):
        source = (params or {}).get("source")
        if source in failing_sources:
            raise requests.RequestException(f"boom for {source}")
        response = MagicMock()
        response.json.return_value = payload_by_source.get(source, {"scanners": []})
        response.raise_for_status.return_value = None
        return response

    session.get.side_effect = _get
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    return session


class TestFetchScannerMap:
    """Behaviour of the cached scanner ID to name lookup."""

    def test_merges_scanners_across_all_sources(self):
        payloads = {
            "vendor": {"scanners": [{"id": "s1", "name": "Prompt Injection"}]},
            "system": {"scanners": [{"id": "s2", "name": "PII"}]},
            "internal": {"scanners": [{"id": "s3", "name": "Custom"}]},
        }
        session = _mock_session(payloads)

        with patch("prompt_evaluator.requests.Session", return_value=session):
            result = pe.fetch_scanner_map()

        assert result == {"s1": "Prompt Injection", "s2": "PII", "s3": "Custom"}
        # One request per known source.
        assert session.get.call_count == len(pe.SCANNER_SOURCES)

    def test_every_request_sends_a_timeout(self):
        """A request without a timeout can hang the whole evaluation run."""
        session = _mock_session({})

        with patch("prompt_evaluator.requests.Session", return_value=session):
            pe.fetch_scanner_map()

        assert session.get.call_count > 0
        for call in session.get.call_args_list:
            assert call.kwargs.get("timeout") == pe.SCANNER_REQUEST_TIMEOUT

    def test_result_is_cached_across_calls(self):
        payloads = {"vendor": {"scanners": [{"id": "s1", "name": "One"}]}}
        session = _mock_session(payloads)

        with patch("prompt_evaluator.requests.Session", return_value=session):
            first = pe.fetch_scanner_map()
            second = pe.fetch_scanner_map()

        assert first == second
        # Still only one pass over the sources; the second call hit the cache.
        assert session.get.call_count == len(pe.SCANNER_SOURCES)

    def test_force_refresh_requeries_the_api(self):
        payloads = {"vendor": {"scanners": [{"id": "s1", "name": "One"}]}}
        session = _mock_session(payloads)

        with patch("prompt_evaluator.requests.Session", return_value=session):
            pe.fetch_scanner_map()
            pe.fetch_scanner_map(force_refresh=True)

        assert session.get.call_count == len(pe.SCANNER_SOURCES) * 2

    def test_one_failing_source_does_not_discard_the_others(self):
        payloads = {
            "vendor": {"scanners": [{"id": "s1", "name": "Kept"}]},
            "system": {"scanners": [{"id": "s2", "name": "Also kept"}]},
        }
        session = _mock_session(payloads, failing_sources=("system",))

        with patch("prompt_evaluator.requests.Session", return_value=session):
            result = pe.fetch_scanner_map()

        assert result == {"s1": "Kept"}

    def test_total_failure_returns_empty_map_and_caches_it(self):
        session = _mock_session({}, failing_sources=pe.SCANNER_SOURCES)

        with patch("prompt_evaluator.requests.Session", return_value=session):
            result = pe.fetch_scanner_map()
            pe.fetch_scanner_map()

        assert result == {}
        # The empty result is cached, so the failing sources are not retried.
        assert session.get.call_count == len(pe.SCANNER_SOURCES)

    def test_scanner_without_a_name_falls_back_to_its_id(self):
        payloads = {"vendor": {"scanners": [{"id": "s1"}, {"id": "s2", "name": None}]}}
        session = _mock_session(payloads)

        with patch("prompt_evaluator.requests.Session", return_value=session):
            result = pe.fetch_scanner_map()

        assert result == {"s1": "s1", "s2": "s2"}

    def test_entries_without_an_id_are_skipped(self):
        payloads = {"vendor": {"scanners": [{"name": "No id"}, {"id": "s1", "name": "Good"}]}}
        session = _mock_session(payloads)

        with patch("prompt_evaluator.requests.Session", return_value=session):
            result = pe.fetch_scanner_map()

        assert result == {"s1": "Good"}


class TestExtractTriggeredScanners:
    """Selection and labelling of the scanners that flagged a prompt."""

    def test_returns_only_scanners_that_did_not_pass(self):
        payload = {
            "scannerResults": [
                {"scannerId": "s1", "outcome": "passed"},
                {"scannerId": "s2", "outcome": "failed"},
            ]
        }
        assert pe.extract_triggered_scanners(payload, {"s1": "A", "s2": "B"}) == ["B"]

    def test_passed_check_is_case_insensitive(self):
        payload = {"scannerResults": [{"scannerId": "s1", "outcome": "PASSED"}]}
        assert pe.extract_triggered_scanners(payload, {"s1": "A"}) == []

    def test_unknown_id_falls_back_to_the_raw_id(self):
        """Preserving the ID beats replacing it with a placeholder."""
        payload = {"scannerResults": [{"scannerId": "unmapped", "outcome": "failed"}]}
        assert pe.extract_triggered_scanners(payload, {"s1": "A"}) == ["unmapped"]

    def test_missing_map_returns_raw_ids(self):
        payload = {"scannerResults": [{"scannerId": "s1", "outcome": "failed"}]}
        assert pe.extract_triggered_scanners(payload) == ["s1"]

    def test_scanner_without_an_outcome_counts_as_triggered(self):
        payload = {"scannerResults": [{"scannerId": "s1"}]}
        assert pe.extract_triggered_scanners(payload, {"s1": "A"}) == ["A"]

    def test_entry_without_a_scanner_id_is_skipped(self):
        payload = {"scannerResults": [{"outcome": "failed"}]}
        assert pe.extract_triggered_scanners(payload, {}) == []

    def test_order_from_the_api_is_preserved(self):
        payload = {
            "scannerResults": [
                {"scannerId": "s3", "outcome": "failed"},
                {"scannerId": "s1", "outcome": "failed"},
            ]
        }
        mapping = {"s1": "One", "s3": "Three"}
        assert pe.extract_triggered_scanners(payload, mapping) == ["Three", "One"]

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"scannerResults": None},
            {"scannerResults": []},
            {"scannerResults": "not-a-list"},
        ],
    )
    def test_malformed_payloads_yield_an_empty_list(self, payload):
        assert pe.extract_triggered_scanners(payload, {"s1": "A"}) == []

    def test_non_dict_entries_are_skipped(self):
        payload = {"scannerResults": ["junk", {"scannerId": "s1", "outcome": "failed"}]}
        assert pe.extract_triggered_scanners(payload, {"s1": "A"}) == ["A"]


class TestCalypsoaiScanScannerField:
    """The scan helper surfaces triggered scanners alongside the outcome."""

    def _mock_post(self, body):
        response = MagicMock()
        response.json.return_value = body
        response.raise_for_status.return_value = None
        return response

    def test_scan_reports_resolved_scanner_names(self):
        body = {
            "result": {
                "outcome": "flagged",
                "scannerResults": [
                    {"scannerId": "s1", "outcome": "failed"},
                    {"scannerId": "s2", "outcome": "passed"},
                ],
            }
        }

        with patch("prompt_evaluator.requests.post", return_value=self._mock_post(body)):
            result = pe.calypsoai_scan("hello", {"s1": "Prompt Injection", "s2": "PII"})

        assert result["outcome"] == "flagged"
        assert result["scanners"] == ["Prompt Injection"]
        assert result["response_time"] >= 0

    def test_response_without_a_result_block_is_handled(self):
        """Older or mocked responses must not raise."""
        with patch("prompt_evaluator.requests.post", return_value=self._mock_post({})):
            result = pe.calypsoai_scan("hello")

        assert result["outcome"] == "no_result"
        assert result["scanners"] == []

    def test_non_dict_result_block_is_handled(self):
        body = {"result": "unexpected"}
        with patch("prompt_evaluator.requests.post", return_value=self._mock_post(body)):
            result = pe.calypsoai_scan("hello")

        assert result["outcome"] == "no_result"
        assert result["scanners"] == []


class TestScannerSerialisation:
    """Flat output formats need the scanner list collapsed into one cell."""

    def test_format_scanners_joins_a_list(self):
        assert pe._format_scanners(["A", "B"]) == "A; B"

    def test_format_scanners_handles_empty_and_none(self):
        assert pe._format_scanners([]) == ""
        assert pe._format_scanners(None) == ""

    def test_format_scanners_passes_through_a_plain_string(self):
        assert pe._format_scanners("A") == "A"

    def test_csv_output_includes_the_scanners_column(self, tmp_path):
        out = tmp_path / "results.csv"
        records = [
            {
                "prompt": "p1",
                "expected": "true",
                "outcome": "flagged",
                "scanners": ["Prompt Injection", "PII"],
                "response_time": 0.1,
                "prompt_size": 2,
                "original_line": 1,
            }
        ]

        pe.write_results_to_file(records, str(out), "csv")

        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert "scanners" in rows[0]
        assert rows[0]["scanners"] == "Prompt Injection; PII"

    def test_tsv_output_includes_the_scanners_column(self, tmp_path):
        out = tmp_path / "results.tsv"
        records = [
            {
                "prompt": "p1",
                "expected": "true",
                "outcome": "flagged",
                "scanners": ["Prompt Injection"],
                "response_time": 0.1,
                "prompt_size": 2,
                "original_line": 1,
            }
        ]

        pe.write_results_to_file(records, str(out), "tsv")
        lines = out.read_text(encoding="utf-8").splitlines()

        header = lines[0].split("\t")
        assert "scanners" in header
        assert lines[1].split("\t")[header.index("scanners")] == "Prompt Injection"

    def test_empty_csv_still_writes_the_scanners_header(self, tmp_path):
        out = tmp_path / "empty.csv"
        pe.write_results_to_file([], str(out), "csv")
        assert "scanners" in out.read_text(encoding="utf-8").splitlines()[0]

    def test_empty_tsv_still_writes_the_scanners_header(self, tmp_path):
        out = tmp_path / "empty.tsv"
        pe.write_results_to_file([], str(out), "tsv")
        assert "scanners" in out.read_text(encoding="utf-8").splitlines()[0]

    def test_jsonl_output_keeps_the_native_list(self, tmp_path):
        import json

        out = tmp_path / "results.jsonl"
        records = [{"prompt": "p1", "outcome": "flagged", "scanners": ["A", "B"]}]

        pe.write_results_to_file(records, str(out), "json")
        written = json.loads(out.read_text(encoding="utf-8").strip())

        assert written["scanners"] == ["A", "B"]

    def test_record_missing_scanners_writes_an_empty_cell(self, tmp_path):
        """Records produced before this feature must still serialise."""
        out = tmp_path / "legacy.csv"
        records = [{"prompt": "p1", "expected": "true", "outcome": "cleared"}]

        pe.write_results_to_file(records, str(out), "csv")

        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert rows[0]["scanners"] == ""


class TestScanPromptsNodeIntegration:
    """The batch node resolves the map once and attaches it to every record."""

    def test_map_is_fetched_once_per_run(self):
        node = pe.ScanPromptsNode()
        shared = {"dataset": [{"prompt": "a", "expected": "true", "original_line": 1}]}

        with patch("prompt_evaluator.fetch_scanner_map", return_value={"s1": "A"}) as mock_fetch:
            node.prep(shared)

        mock_fetch.assert_called_once()
        assert node.scanner_map == {"s1": "A"}

    def test_opt_out_skips_the_lookup_entirely(self):
        node = pe.ScanPromptsNode()
        shared = {
            "dataset": [{"prompt": "a", "expected": "true", "original_line": 1}],
            "resolve_scanner_names": False,
        }

        with patch("prompt_evaluator.fetch_scanner_map") as mock_fetch:
            node.prep(shared)

        mock_fetch.assert_not_called()
        assert node.scanner_map == {}

    def test_empty_dataset_does_not_trigger_a_lookup(self):
        node = pe.ScanPromptsNode()

        with patch("prompt_evaluator.fetch_scanner_map") as mock_fetch:
            assert node.prep({"dataset": []}) == []

        mock_fetch.assert_not_called()

    def test_failed_scan_record_still_carries_a_scanners_key(self):
        node = pe.ScanPromptsNode()
        node.total_prompts = 1

        with patch("prompt_evaluator.calypsoai_scan", side_effect=RuntimeError("api down")):
            record = node.exec({"prompt": "a", "expected": "true", "original_line": 1})

        assert record["scanners"] == []
        assert record["outcome"].startswith("error:")
