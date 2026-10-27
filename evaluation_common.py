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

"""Shared binary detection policy and backward-readable result serialization.

Enforcement outcomes stay unchanged on disk. Scoring treats flagged, blocked, and
redacted as detections; operational failures are not positive or negative labels.
"""

import csv
import json
import math
from pathlib import Path

POSITIVE_OUTCOMES = frozenset(("flagged", "blocked", "redacted"))
STRUCTURED_FIELDS = frozenset(
    ("metadata", "scanner_results", "provider_result", "scanners")
)
BASE_FIELDS = [
    "prompt",
    "expected",
    "outcome",
    "response_time",
    "prompt_size",
    "original_line",
    "metadata",
]
FORMAT_EXTENSIONS = {"json": "jsonl", "csv": "csv", "tsv": "tsv", "parquet": "parquet"}


def normalize_expected(value):
    """Return a binary string or None; accept booleans and existing label aliases."""
    text = str(value).strip().lower()
    if text in ("true", "injection", "malicious", "attack"):
        return "true"
    if text in ("false", "benign", "safe", "normal"):
        return "false"
    return None


def normalize_outcome(value):
    """Return the binary policy value without altering the original API outcome."""
    text = str(value).strip().lower()
    if text in POSITIVE_OUTCOMES:
        return "flagged"
    return "cleared" if text == "cleared" else None


def _decode_json(value):
    """Decode JSON cells only; historical Python repr strings remain opaque."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return value


def record_category(record):
    """Return tp/tn/fp/fn or an explicit error/incomplete/invalid exclusion."""
    raw = str(record.get("outcome", "")).strip().lower()
    status = record.get("status")
    if status == "error" or raw == "error" or raw.startswith("error:"):
        return "error"
    scans = _decode_json(record.get("scanner_results", []))
    if status == "incomplete" or (
        isinstance(scans, list)
        and any(
            isinstance(scan, dict)
            and isinstance(scan.get("data"), dict)
            and scan["data"].get("type") == "error"
            for scan in scans
        )
    ):
        return "incomplete"
    expected = normalize_expected(record.get("expected"))
    outcome = normalize_outcome(raw)
    if status not in (None, "", "ok") or expected is None or outcome is None:
        return "invalid"
    return {
        ("true", "flagged"): "tp",
        ("false", "cleared"): "tn",
        ("false", "flagged"): "fp",
        ("true", "cleared"): "fn",
    }[(expected, outcome)]


def calculate_metrics(records):
    """Score iterable rows with total=evaluated and explicit mutually exclusive exclusions."""
    counts = dict.fromkeys(
        ("tp", "tn", "fp", "fn", "error", "incomplete", "invalid"), 0
    )
    distribution: dict[str, int] = {}
    provider_errors = 0
    opaque_evidence = 0
    for record in records:
        counts[record_category(record)] += 1
        outcome = str(record.get("outcome", "")).strip().lower()
        distribution[outcome] = distribution.get(outcome, 0) + 1
        provider_errors += str(record.get("provider_error", False)).lower() == "true"
        evidence = _decode_json(record.get("scanner_results"))
        opaque_evidence += isinstance(evidence, str) and bool(evidence.strip())
    tp, tn, fp, fn = (counts[key] for key in ("tp", "tn", "fp", "fn"))
    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "total": total,
        "evaluated_count": total,
        "attempted_count": sum(counts.values()),
        "error_count": counts["error"],
        "incomplete_count": counts["incomplete"],
        "invalid_count": counts["invalid"],
        "excluded_count": counts["error"] + counts["incomplete"] + counts["invalid"],
        "provider_error_count": provider_errors,
        "scanner_evidence_unavailable_count": opaque_evidence,
        "accuracy": (tp + tn) / total if total else 0.0,
        "precision": precision,
        "recall": recall,
        "f1_score": (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        ),
        "outcome_distribution": distribution,
    }


def false_results(records):
    """Derive both misclassification lists from the same rows used for metrics."""
    return (
        [row for row in records if record_category(row) == "fp"],
        [row for row in records if record_category(row) == "fn"],
    )


def sample_record(item, result):
    """Retain input provenance on success and failure, with response evidence taking precedence."""
    return (
        {
            key: item[key]
            for key in (
                "prompt",
                "expected",
                "original_line",
                "id",
                "metadata",
                "timestamp",
            )
            if key in item
        }
        | {
            "prompt_size": (
                len(item["prompt"]) if isinstance(item.get("prompt"), str) else None
            )
        }
        | result
    )


def error_result(item, error):
    """Construct a failure row without storing arbitrary exception or server content."""
    from calypsoai_client import safe_error_record

    return sample_record(
        item,
        {
            "outcome": "error",
            "status": "error",
            "response_time": None,
            "scanner_results": [],
            **safe_error_record(error),
        },
    )


def valid_response_times(records):
    """Return finite, nonnegative request durations for completed, evaluable rows."""
    durations = []
    for record in records:
        if record_category(record) not in ("tp", "tn", "fp", "fn"):
            continue
        try:
            value = float(record.get("response_time"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(value) and value >= 0:
            durations.append(value)
    return durations


def result_path(input_file, format_type="json", output_file=None, suffix=""):
    """Resolve a default or explicit filename confined to the current results directory."""
    if format_type not in FORMAT_EXTENSIONS:
        raise ValueError("Unsupported results format")
    root = Path("results").resolve()
    if output_file:
        supplied = Path(output_file)
        path = (
            supplied
            if supplied.is_absolute() or supplied.parts[0] == "results"
            else root / supplied
        )
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError("Output files must remain within results/")
        expected = "." + FORMAT_EXTENSIONS[format_type]
        if path.suffix.lower() != expected:
            raise ValueError(
                f"Output extension must be {expected} for the selected format"
            )
    else:
        path = (
            root
            / f"{Path(input_file).stem}{suffix}_results.{FORMAT_EXTENSIONS[format_type]}"
        )
    if path.resolve() == Path(input_file).resolve():
        raise ValueError("Output must not overwrite the input dataset")
    reserved = {
        f"{Path(input_file).stem}{suffix}_false_{kind}.{extension}"
        for kind in ("positives", "negatives")
        for extension in FORMAT_EXTENSIONS.values()
    }
    if path.name in reserved:
        raise ValueError(
            "Output filename collides with a false-positive/negative export"
        )
    return str(path)


def dataset_inputs(shared, default_format="json", suffix=""):
    """Validate paths/formats/limits before reading inputs or making any API call."""
    input_file = shared.get("input_file", "prompt_inject_dataset.csv")
    main_path = result_path(
        input_file,
        shared.get("results_format", default_format),
        shared.get("output_file"),
        suffix,
    )
    if shared.get("output_format", "json") not in FORMAT_EXTENSIONS:
        raise ValueError("Unsupported export format")
    export_format = shared.get("output_format", "json")
    export_paths = [
        Path("results")
        / f"{Path(input_file).stem}{suffix}_false_{kind}.{FORMAT_EXTENSIONS[export_format]}"
        for kind in ("positives", "negatives")
    ]
    resolved = [Path(main_path).resolve(), Path(input_file).resolve()]
    resolved.extend(path.resolve() for path in export_paths)
    if len(set(resolved)) != len(resolved):
        raise ValueError("Input, main result, and export paths must not overlap")
    if "parquet" in (shared.get("results_format", default_format), export_format):
        from importlib.util import find_spec

        if not any(
            find_spec(engine) is not None for engine in ("pyarrow", "fastparquet")
        ):
            raise ValueError(
                "Parquet requires an engine: install requirements-parquet.txt"
            )
    limit = shared.get("max_lines")
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError("Input line limit must be a positive integer")
    return input_file, limit, shared.get("format_hint")


def load_dataset_inputs(inputs):
    """Abort empty/unreadable inputs before output writes; never echo raw reader warnings."""
    import contextlib
    import io
    from tools.enhanced_dataset_reader import load_dataset_enhanced

    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        dataset = load_dataset_enhanced(*inputs)
    if not dataset:
        raise ValueError("Input dataset contains no usable records")
    warnings = sum(line.startswith("Warning:") for line in log.getvalue().splitlines())
    if warnings:
        print(
            f"Dataset reader reported {warnings} warnings; inspect the source input locally."
        )
    print(f"Loaded {len(dataset)} usable records")
    return dataset


def write_results_to_file(data, file_path, format_type):
    """Write rows without fixed-column data loss; nested tabular cells use JSON.

    Parquet requires an optional engine. Missing engines fail clearly rather than
    silently changing the requested filename/format. Empty tables retain headers.
    """
    if format_type not in FORMAT_EXTENSIONS:
        raise ValueError("Unsupported results format")
    data = list(data)
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if format_type == "json":
        with path.open("w", encoding="utf-8") as stream:
            for row in data:
                stream.write(
                    json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n"
                )
        return str(path)
    fields = BASE_FIELDS + list(
        dict.fromkeys(key for row in data for key in row if key not in BASE_FIELDS)
    )
    rows = [
        {
            key: (
                json.dumps(value, ensure_ascii=False, allow_nan=False)
                if isinstance(value, (dict, list))
                else value
            )
            for key, value in row.items()
        }
        for row in data
    ]
    if format_type in ("csv", "tsv"):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fields,
                delimiter="\t" if format_type == "tsv" else ",",
            )
            writer.writeheader()
            writer.writerows(rows)
    else:
        import pandas as pd

        # Tabular labels may mix JSON booleans and invalid strings. Use strings,
        # as CSV/TSV do, so Arrow preserves every row for exclusion accounting.
        for row in rows:
            if row.get("expected") is not None:
                row["expected"] = str(row["expected"])

        try:
            pd.DataFrame(rows, columns=fields).to_parquet(path, index=False)
        except ImportError:
            raise ValueError(
                "Parquet requires an engine: install requirements-parquet.txt"
            ) from None
    return str(path)


def read_results(file_path):
    """Read historical/new JSONL, CSV, TSV, or Parquet without executing cell content."""
    path = Path(file_path)
    if path.suffix.lower() in (".json", ".jsonl"):
        rows = []
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    row = {"status": "invalid", "outcome": "invalid_record"}
                rows.append(row if isinstance(row, dict) else {"status": "invalid"})
    elif path.suffix.lower() in (".csv", ".tsv"):
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(
                csv.DictReader(
                    stream, delimiter="\t" if path.suffix.lower() == ".tsv" else ","
                )
            )
    elif path.suffix.lower() == ".parquet":
        import pandas as pd

        try:
            frame = pd.read_parquet(path)
        except ImportError:
            raise ValueError(
                "Parquet requires an engine: install requirements-parquet.txt"
            ) from None
        rows = frame.astype(object).where(frame.notna(), None).to_dict("records")
    else:
        raise ValueError("Supported result formats: JSONL, CSV, TSV, Parquet")
    for row in rows:
        for key in STRUCTURED_FIELDS & row.keys():
            row[key] = _decode_json(row[key])
    return rows


def format_metrics(metrics):
    """Format common CLI counts/rates; all-error runs still show their exclusions."""
    return (
        "\nEvaluation Results:\n------------------\n"
        f"Attempted Samples: {metrics['attempted_count']}\n"
        f"Evaluated Samples: {metrics['total']}\n"
        f"Errors: {metrics['error_count']}\n"
        f"Incomplete: {metrics['incomplete_count']}\n"
        f"Invalid: {metrics['invalid_count']}\n"
        f"Provider failures (separate): {metrics['provider_error_count']}\n"
        f"Opaque legacy scanner evidence: {metrics['scanner_evidence_unavailable_count']}\n"
        f"True Positives: {metrics['true_positive']}\n"
        f"True Negatives: {metrics['true_negative']}\n"
        f"False Positives: {metrics['false_positive']}\n"
        f"False Negatives: {metrics['false_negative']}\n"
        f"Overall Accuracy: {metrics['accuracy']:.2%}\n"
        f"Precision: {metrics['precision']:.2%}\n"
        f"Recall: {metrics['recall']:.2%}\n"
        f"F1 Score: {metrics['f1_score']:.2%}\n"
    )


def add_api_arguments(parser, prompts=False):
    """Add supported project/provider selection and bounded-request CLI controls."""
    parser.add_argument(
        "--project", help="Project name or ID (default: global project)"
    )
    if prompts:
        parser.add_argument(
            "--provider", help="Provider name or ID (default: project default)"
        )
    parser.add_argument(
        "--timeout",
        type=float,
        help="Request timeout in seconds (default: 30 or CALYPSOAI_TIMEOUT)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=prompts,
        help="Request per-guardrail details (enabled for prompts)",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Retain extra diagnostic content; output may contain sensitive data",
    )
    parser.add_argument(
        "--format-hint",
        choices=("jsonl", "csv", "tsv", "pipe", "parquet"),
        help="Explicit input format, including legacy pipe-delimited .csv files",
    )


def request_options(shared, prompts=False):
    """Resolve one immutable configuration per run; direct node users may supply config."""
    from calypsoai_client import APIConfig

    options = {
        "config": shared.get("api_config")
        or APIConfig.from_environment(shared.get("timeout")),
        "project": shared.get("project"),
        "verbose": shared.get("verbose", prompts),
        "diagnostics": shared.get("diagnostics", False),
    }
    if prompts:
        options["provider"] = shared.get("provider")
    return options


def latency_statistics(records, total_time=None):
    """Summarize evaluable request durations; unavailable wall time stays unavailable."""
    import numpy as np

    times = valid_response_times(records)
    if not times:
        return None
    stats = {
        "average_latency": float(np.mean(times)),
        "min_latency": min(times),
        "max_latency": max(times),
        "p50_latency": float(np.percentile(times, 50)),
        "p95_latency": float(np.percentile(times, 95)),
        "p99_latency": float(np.percentile(times, 99)),
        "total_prompts": len(records),
    }
    if total_time is not None:
        stats["total_time"] = total_time
        stats["throughput"] = len(records) / total_time if total_time > 0 else 0.0
    return stats


def format_latency(records, total_time=None):
    """Render aggregate timings without echoing potentially sensitive prompt samples."""
    stats = latency_statistics(records, total_time)
    if stats is None:
        return "No evaluable response-time data available."
    output = "\nRequest latency (evaluable rows):\n"
    for key, label in (
        ("average_latency", "Average"),
        ("min_latency", "Minimum"),
        ("max_latency", "Maximum"),
        ("p50_latency", "p50"),
        ("p95_latency", "p95"),
        ("p99_latency", "p99"),
    ):
        output += f"{label}: {stats[key] * 1000:.2f} ms\n"
    if total_time is not None:
        output += f"Attempt throughput: {stats['throughput']:.2f} prompts/sec\n"
    return output
