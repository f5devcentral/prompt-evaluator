# Copyright 2026 Andy Ryan
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

"""Shared-policy, result round-trip, workflow, concurrency, and report regressions."""

import importlib
import json
import time

import pytest
import requests

from calypsoai_client import APIConfig
from evaluation_common import (
    calculate_metrics,
    false_results,
    format_metrics,
    latency_statistics,
    read_results,
    record_category,
    result_path,
    write_results_to_file,
)
from tests.contract_fixtures import FakeResponse, api_body


def rows():
    """Return mixed synthetic successes/exclusions with distinct FP/FN counts."""
    values = [
        (True, "flagged"),
        (False, "cleared"),
        (False, "blocked"),
        (True, "redacted"),
        (True, "cleared"),
        (True, "cleared"),
        (True, "error: historical failure"),
        (True, "unknown"),
        ("invalid-label", "cleared"),
    ]
    records = [
        {
            "id": str(i),
            "prompt": 'synthetic |\t"quoted"\nUnicode é',
            "expected": label,
            "outcome": outcome,
            "response_time": 0.1,
            "prompt_size": 12,
            "metadata": {"source": "synthetic"},
            "scanner_results": [],
            "timestamp": "2025-01-01T00:00:00Z",
        }
        for i, (label, outcome) in enumerate(values)
    ]
    records.append(
        dict(records[0], id="incomplete", scanner_results=[{"data": {"type": "error"}}])
    )
    return records


def test_accounting_policy_and_invalid_rows():
    """Every row belongs to the confusion matrix or exactly one visible exclusion."""
    metrics = calculate_metrics(rows())
    assert metrics["attempted_count"] == 10
    assert metrics["total"] == 6
    assert [
        metrics[key]
        for key in (
            "true_positive",
            "true_negative",
            "false_positive",
            "false_negative",
        )
    ] == [2, 1, 1, 2]
    assert metrics["accuracy"] == 0.5
    assert (
        metrics["error_count"],
        metrics["incomplete_count"],
        metrics["invalid_count"],
    ) == (1, 1, 2)
    assert metrics["attempted_count"] == metrics["total"] + metrics["excluded_count"]
    assert "Attempted Samples: 10" in format_metrics(metrics)
    assert calculate_metrics([])["total"] == 0
    assert record_category({"expected": "safe", "outcome": " BLOCKED "}) == "fp"
    assert record_category({"expected": "attack", "outcome": "redacted"}) == "tp"


@pytest.mark.parametrize(
    "format_type,extension",
    [("json", "jsonl"), ("csv", "csv"), ("tsv", "tsv"), ("parquet", "parquet")],
)
def test_round_trip_metrics_and_reports(tmp_path, format_type, extension):
    """All formats retain raw outcomes/evidence and agree with online/offline reports."""
    if format_type == "parquet":
        pytest.importorskip("pyarrow")
    from evaluate_existing_results import evaluate_existing_results
    from report_generator import load_evaluation_results
    from comparative_report_generator import compute_metrics

    original = rows()
    path = tmp_path / f"synthetic_results.{extension}"
    write_results_to_file(iter(original), path, format_type)
    restored = read_results(path)
    metrics = calculate_metrics(original)
    assert calculate_metrics(restored) == metrics
    assert evaluate_existing_results(path) == metrics
    loaded = load_evaluation_results("synthetic", str(tmp_path))
    assert loaded["metrics"] == metrics
    expected_fp, expected_fn = false_results(original)
    assert [row["id"] for row in loaded["false_positives"]] == [
        row["id"] for row in expected_fp
    ]
    assert [row["id"] for row in loaded["false_negatives"]] == [
        row["id"] for row in expected_fn
    ]
    assert restored[0]["metadata"] == original[0]["metadata"]
    assert restored[0]["prompt"] == original[0]["prompt"]
    assert restored[2]["outcome"] == "blocked"
    comparative = compute_metrics(restored)
    assert comparative["total"] == metrics["total"]
    assert comparative["accuracy"] == metrics["accuracy"]
    assert comparative["tp"] == metrics["true_positive"]


def test_malformed_jsonl_and_legacy_opaque_scanners(tmp_path):
    """Malformed rows count invalid; historical Python repr stays opaque, never evaluated."""
    path = tmp_path / "legacy.jsonl"
    path.write_text('not json\n[]\n{"expected":"true","outcome":"blocked"}\n')
    metrics = calculate_metrics(read_results(path))
    assert metrics["attempted_count"] == 3
    assert metrics["invalid_count"] == 2
    assert metrics["true_positive"] == 1
    legacy = {
        "expected": "true",
        "outcome": "flagged",
        "scanner_results": "[{'data': {'type': 'error'}}]",
    }
    # Legacy repr is deliberately not interpreted; only the historical aggregate is available.
    assert record_category(legacy) == "tp"
    assert calculate_metrics([legacy])["scanner_evidence_unavailable_count"] == 1
    encoded = dict(legacy, scanner_results='[{"data":{"type":"error"}}]')
    assert record_category(encoded) == "incomplete"


@pytest.mark.parametrize("format_type", ["json", "csv", "tsv", "parquet"])
def test_empty_outputs_and_optional_engine(tmp_path, format_type, monkeypatch):
    """Empty outputs remain readable; missing Parquet engines do not change formats silently."""
    if format_type == "parquet":
        pytest.importorskip("pyarrow")
    extension = "jsonl" if format_type == "json" else format_type
    path = tmp_path / f"empty.{extension}"
    write_results_to_file([], path, format_type)
    assert read_results(path) == []
    if format_type == "parquet":
        import pandas as pd

        def missing(*a, **kw):
            raise ImportError("no engine")

        monkeypatch.setattr(pd.DataFrame, "to_parquet", missing)
        with pytest.raises(ValueError, match="requirements-parquet"):
            write_results_to_file(rows(), tmp_path / "no-engine.parquet", "parquet")
        monkeypatch.setattr(pd, "read_parquet", missing)
        with pytest.raises(ValueError, match="requirements-parquet"):
            read_results(tmp_path / "no-engine.parquet")


def test_output_names_and_escaping(tmp_path, monkeypatch):
    """Explicit output stays in results/ and must agree with the selected format."""
    monkeypatch.chdir(tmp_path)
    assert result_path("a.jsonl").endswith("results/a_results.jsonl")
    assert result_path("a.jsonl", suffix="_concurrent").endswith(
        "a_concurrent_results.jsonl"
    )
    assert result_path("a.jsonl", "csv", "custom.csv").endswith("results/custom.csv")
    for output in (
        "../outside.jsonl",
        "/tmp/outside.jsonl",
        "results/../../outside.jsonl",
    ):
        with pytest.raises(ValueError):
            result_path("a.jsonl", "json", output)
    with pytest.raises(ValueError):
        result_path("a.jsonl", "json", "custom.csv")
    with pytest.raises(ValueError, match="collides"):
        result_path("a.jsonl", "json", "a_false_positives.jsonl")
    with pytest.raises(ValueError, match="overwrite"):
        result_path("results/a.jsonl", "json", "a.jsonl")
    with pytest.raises(ValueError):
        write_results_to_file([], tmp_path / "bad", "bad")
    with pytest.raises(ValueError):
        read_results(tmp_path / "bad.xyz")


@pytest.mark.parametrize(
    "module",
    ["prompt_evaluator", "prompt_evaluator_prompts", "prompt_evaluator_concurrent"],
)
@pytest.mark.parametrize("format_type", ["json", "csv", "tsv", "parquet"])
def test_actual_workflow_round_trip(tmp_path, monkeypatch, module, format_type):
    """Run real workflow nodes with synthetic transport and verify every saved classification."""
    if format_type == "parquet":
        pytest.importorskip("pyarrow")
    monkeypatch.chdir(tmp_path)
    evaluator = importlib.import_module(module)
    prompts = module.endswith("_prompts")
    concurrent = module.endswith("_concurrent")
    dataset = [
        {
            "prompt": outcome,
            "expected": label,
            "id": str(i),
            "metadata": {"source": "synthetic"},
            "timestamp": "2025-01-01T00:00:00Z",
        }
        for i, (label, outcome) in enumerate(
            [
                (True, "flagged"),
                (False, "cleared"),
                (False, "blocked"),
                (True, "redacted"),
                (True, "cleared"),
                (True, "error"),
                (True, "incomplete"),
            ]
        )
    ]
    input_file = tmp_path / "synthetic.jsonl"
    input_file.write_text("".join(json.dumps(row) + "\n" for row in dataset))
    calls = []

    def post(*args, **kwargs):
        calls.append(kwargs)
        outcome = kwargs["json"]["input"]
        if outcome == "error":
            return FakeResponse(status=422)
        return FakeResponse(
            api_body(
                "prompts" if prompts else "scans",
                "flagged" if outcome == "incomplete" else outcome,
                error=outcome == "incomplete",
            )
        )

    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr(requests.Session, "post", post)
    shared = {
        "input_file": str(input_file),
        "results_format": format_type,
        "output_format": format_type,
        "skip_pdf": True,
        "api_config": APIConfig("https://offline.invalid/backend/v1", "synthetic"),
        "project": "test-project",
        "provider": "test-provider",
    }
    flow = (
        evaluator.create_concurrent_evaluation_flow(2)
        if concurrent
        else evaluator.create_evaluation_flow()
    )
    flow.run(shared)
    records = shared["prompt_results" if prompts else "scan_results"]
    assert len(calls) == len(dataset)
    assert all(call["timeout"] == 30 for call in calls)
    assert all(call["json"]["project"] == "test-project" for call in calls)
    if prompts:
        assert all(call["json"]["provider"] == "test-provider" for call in calls)
    assert (
        calculate_metrics(read_results(shared["output_file"]))
        == shared["evaluation_results"]
    )
    assert shared["evaluation_results"]["total"] == 5
    assert shared["evaluation_results"]["error_count"] == 1
    assert shared["evaluation_results"]["incomplete_count"] == 1
    assert {row["id"] for row in records} == {row["id"] for row in dataset}
    assert all(row["timestamp"] == "2025-01-01T00:00:00Z" for row in records)
    assert all(row["metadata"] == {"source": "synthetic"} for row in records)
    extension = "jsonl" if format_type == "json" else format_type
    prefix = "synthetic_concurrent" if concurrent else "synthetic"
    fp_file = tmp_path / "results" / f"{prefix}_false_positives.{extension}"
    fn_file = tmp_path / "results" / f"{prefix}_false_negatives.{extension}"
    fps, fns = false_results(records)
    assert {r["id"] for r in read_results(fp_file)} == {r["id"] for r in fps}
    assert {r["id"] for r in read_results(fn_file)} == {r["id"] for r in fns}


def test_concurrent_real_queue_wait_and_out_of_order(monkeypatch):
    """A queued task includes executor wait, and reordered completion retains original IDs."""
    from prompt_evaluator_concurrent import ConcurrentScanPromptsNode

    def post(*a, **kw):
        time.sleep(0.04 if kw["json"]["input"] == "slow" else 0.001)
        return FakeResponse(api_body())

    monkeypatch.setattr(requests.Session, "post", post)
    items = [
        {"prompt": name, "expected": True, "id": name}
        for name in ("slow", "fast", "third")
    ]
    node = ConcurrentScanPromptsNode(1)
    shared = {
        "dataset": items,
        "api_config": APIConfig("https://offline.invalid/backend/v1", "synthetic"),
    }
    records = node.exec(node.prep(shared))
    assert records[1]["queue_time_ms"] >= 20
    assert {row["worker_id"] for row in records} == {0}
    assert records[1]["total_time_ms"] >= records[1]["queue_time_ms"]
    node = ConcurrentScanPromptsNode(2)
    records = node.exec(node.prep(shared))
    assert records[0]["id"] == "fast"
    assert {r["id"] for r in records} == {"slow", "fast", "third"}
    assert not node._sessions
    for value in (0, -1):
        with pytest.raises(ValueError):
            ConcurrentScanPromptsNode(value)
        with pytest.raises(ValueError):
            ConcurrentScanPromptsNode(1, value)


def test_pdf_generation_chart_orientation_and_stale_sidecars(tmp_path, monkeypatch):
    """Generate a synthetic PDF and assert matrix orientation and row-derived FP/FN."""
    from matplotlib.axes import Axes
    from report_generator import PDFReportGenerator, load_evaluation_results

    path = tmp_path / "synthetic_results.jsonl"
    write_results_to_file(rows(), path, "json")
    (tmp_path / "synthetic_false_positives.jsonl").write_text('{"id":"stale"}\n')
    loaded = load_evaluation_results("synthetic", str(tmp_path))
    assert all(row["id"] != "stale" for row in loaded["false_positives"])
    captured = []
    original = Axes.imshow

    def imshow(self, matrix, *a, **kw):
        captured.append(matrix)
        return original(self, matrix, *a, **kw)

    monkeypatch.setattr(Axes, "imshow", imshow)
    output = tmp_path / "synthetic_report.pdf"
    PDFReportGenerator(str(tmp_path)).generate_report(
        "synthetic",
        loaded["metrics"],
        loaded["false_positives"],
        loaded["false_negatives"],
        loaded["latency_stats"],
        str(output),
        evaluation_mode="prompts",
    )
    assert output.read_bytes().startswith(b"%PDF")
    assert captured[-1] == [[2, 2], [1, 1]]
    assert (
        latency_statistics([{"expected": True, "outcome": "error", "response_time": 0}])
        is None
    )


@pytest.mark.parametrize(
    "module",
    ["prompt_evaluator", "prompt_evaluator_prompts", "prompt_evaluator_concurrent"],
)
@pytest.mark.parametrize(
    "case,exit_code", [("success", 0), ("http_error", 2), ("missing_input", 1)]
)
def test_cli_wiring_and_exit_status(tmp_path, monkeypatch, module, case, exit_code):
    """Real CLI dispatch honors config/output flags and returns explicit failure statuses."""
    evaluator = importlib.import_module(module)
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "input.jsonl"
    if case != "missing_input":
        source.write_text('{"prompt":"synthetic","expected":true}\n')
    args = [
        module,
        "-i",
        str(source),
        "--project",
        "chosen-project",
        "--timeout",
        "4",
        "--results-format",
        "json",
        "--output",
        "custom.jsonl",
    ]
    if module.endswith("_prompts"):
        args.extend(["--provider", "chosen-provider"])
    if hasattr(evaluator, "GeneratePDFReportNode"):
        monkeypatch.setattr(evaluator.GeneratePDFReportNode, "exec", lambda *a: None)
    monkeypatch.setattr("sys.argv", args)
    monkeypatch.setattr("builtins.input", lambda *a: "yes")
    calls = []

    def post(*a, **kw):
        calls.append(kw)
        if case == "http_error":
            return FakeResponse(status=422)
        return FakeResponse(
            api_body("prompts" if module.endswith("_prompts") else "scans")
        )

    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr(requests.Session, "post", post)
    assert evaluator.main() == exit_code
    if case == "missing_input":
        assert not calls
        assert not (tmp_path / "results").exists()
    else:
        assert (tmp_path / "results" / "custom.jsonl").exists()
        assert calls[0]["timeout"] == 4
        assert calls[0]["json"]["project"] == "chosen-project"
        if module.endswith("_prompts"):
            assert calls[0]["json"]["provider"] == "chosen-provider"


def test_preflight_export_symlink_and_missing_engine(tmp_path, monkeypatch):
    """Resolved symlink collisions and missing optional engines fail before input/API work."""
    from evaluation_common import dataset_inputs

    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "results"
    directory.mkdir()
    main = directory / "input_results.jsonl"
    main.write_text("previous")
    (directory / "input_false_positives.jsonl").symlink_to(main)
    with pytest.raises(ValueError, match="overlap"):
        dataset_inputs({"input_file": "input.jsonl"})
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    with pytest.raises(ValueError, match="requirements-parquet"):
        dataset_inputs({"input_file": "other.jsonl", "results_format": "parquet"})


def test_offline_validator_and_explicit_api_probe(monkeypatch, tmp_path, capsys):
    """Default validation is offline; explicit probes distinguish permission and connectivity."""
    import validate_setup

    monkeypatch.setattr("sys.argv", ["validate_setup.py"])
    assert validate_setup.main() == 0
    assert "offline default" in capsys.readouterr().out
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({"scanners": []})

    monkeypatch.setattr(requests, "get", get)
    assert validate_setup.check_calypsoai_api()
    assert calls[0][0].endswith("/backend/v1/scanners")
    assert calls[0][1]["params"] == {"limit": 1}
    for status in (401, 403, 422, 500):
        monkeypatch.setattr(
            requests, "get", lambda *a, **kw: FakeResponse(status=status)
        )
        assert not validate_setup.check_calypsoai_api()
    data = tmp_path / "dataset.jsonl"
    data.write_text('{"prompt":"synthetic","expected":true}\n')
    assert validate_setup.check_dataset(str(data))
    assert not validate_setup.check_dataset(str(tmp_path / "missing"))


@pytest.mark.parametrize(
    "module",
    ["prompt_evaluator", "prompt_evaluator_prompts", "prompt_evaluator_concurrent"],
)
@pytest.mark.parametrize(
    "problem", ["missing", "empty", "malformed", "collision", "source_collision"]
)
def test_preflight_preserves_existing_artifacts(tmp_path, monkeypatch, module, problem):
    """Failed loads/path collisions abort before transport and preserve previous file bytes."""
    monkeypatch.chdir(tmp_path)
    evaluator = importlib.import_module(module)
    concurrent = module.endswith("_concurrent")
    suffix = "_concurrent" if concurrent else ""
    directory = tmp_path / "results"
    directory.mkdir()
    input_file = (
        directory if problem == "source_collision" else tmp_path
    ) / "synthetic.jsonl"
    if problem != "missing":
        input_file.write_text(
            ""
            if problem == "empty"
            else (
                "bad JSON"
                if problem == "malformed"
                else '{"prompt":"synthetic","expected":true}\n'
            )
        )
    main_file = directory / f"synthetic{suffix}_results.jsonl"
    fp_file = directory / f"synthetic{suffix}_false_positives.jsonl"
    main_file.write_text("previous main bytes")
    fp_file.write_text("previous export bytes")
    shared = {"input_file": str(input_file), "results_format": "json", "skip_pdf": True}
    if problem == "collision":
        shared["output_file"] = fp_file.name
    if problem == "source_collision":
        shared["output_file"] = input_file.name
    before = {p: p.read_bytes() for p in directory.iterdir()}
    requests_made = []

    def unexpected(*a, **kw):
        requests_made.append(True)
        raise AssertionError("Preflight must not send requests")

    monkeypatch.setattr(requests, "post", unexpected)
    monkeypatch.setattr(requests.Session, "post", unexpected)
    flow = (
        evaluator.create_concurrent_evaluation_flow(2)
        if concurrent
        else evaluator.create_evaluation_flow()
    )
    with pytest.raises((FileNotFoundError, ValueError)):
        flow.run(shared)
    assert not requests_made
    assert {p: p.read_bytes() for p in directory.iterdir()} == before


def test_concurrent_latency_excludes_incomplete_and_invalid_rows():
    """Sequential/PDF and concurrent summaries use the same evaluable timing population."""
    from prompt_evaluator_concurrent import ConcurrentMetricsNode

    valid = {
        "expected": True,
        "outcome": "flagged",
        "response_time": 0.1,
        "request_time_ms": 100,
        "queue_time_ms": 1,
        "total_time_ms": 101,
    }
    incomplete = dict(
        valid, status="incomplete", response_time=10, request_time_ms=10000
    )
    invalid = dict(valid, expected="invalid", response_time=20, request_time_ms=20000)
    _, metrics = ConcurrentMetricsNode().exec(
        ([valid, incomplete, invalid], {"total_time": 2})
    )
    assert (
        metrics["request_latency"]["avg"]
        == latency_statistics([valid, incomplete, invalid])["average_latency"] * 1000
    )
    assert metrics["total_prompts"] == 3


def test_comparative_all_excluded_produces_coverage_pdf(tmp_path, monkeypatch):
    """All-excluded configurations yield a coverage report, not division errors or conclusions."""
    import comparative_report_generator as report

    scores = report.compute_metrics([{"expected": True, "outcome": "error"}])
    data = {
        cfg["key"]: {
            "config": cfg,
            "records": [],
            "metrics": scores,
            "false_positives": [],
            "false_negatives": [],
        }
        for cfg in report.CONFIGS
    }
    output = tmp_path / "coverage.pdf"
    monkeypatch.setattr(report, "load_all_data", lambda: data)
    monkeypatch.setattr(report, "RESULTS_DIR", str(tmp_path))
    monkeypatch.setattr(report, "OUTPUT_PATH", str(output))
    report.main()
    assert output.read_bytes().startswith(b"%PDF")
