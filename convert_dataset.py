# MIT License
#
# Copyright (c) 2025 Andy Ryan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#!/usr/bin/env python3
"""
Dataset Converter

Converts datasets to the format required by the prompt evaluator.
Supports CSV and JSONL input, with JSONL as the default output format.

Handles the 'original_label' field (malicious/benign) by mapping it to
the 'expected' field (true/false) when 'expected' is not already present.

Usage:
    python convert_dataset.py --input datasets/my_dataset.jsonl
    python convert_dataset.py --input data.csv --output datasets/converted.jsonl
    python convert_dataset.py --input data.csv --output-format pipe --legacy
"""

import argparse
import csv
import json
import os
from pathlib import Path


# Mapping from original_label values to expected values
LABEL_TO_EXPECTED = {
    "malicious": "true",
    "benign": "false",
}


def resolve_expected(record):
    """
    Determine the 'expected' value for a record.

    If an 'expected' field is already present, use it as-is.
    Otherwise, derive it from 'original_label' (which may be at the top level
    or nested inside 'metadata').

    Returns the expected value as a lowercase string ("true"/"false"),
    or None if it cannot be determined.
    """
    # Use existing expected field if present
    expected = record.get("expected")
    if expected is not None and str(expected).strip():
        return str(expected).strip().lower()

    # Try top-level original_label
    label = record.get("original_label", "").strip().lower()
    if label in LABEL_TO_EXPECTED:
        return LABEL_TO_EXPECTED[label]

    # Try metadata.original_label
    metadata = record.get("metadata", {})
    if isinstance(metadata, dict):
        label = metadata.get("original_label", "").strip().lower()
        if label in LABEL_TO_EXPECTED:
            return LABEL_TO_EXPECTED[label]

    return None


def read_jsonl(input_file):
    """Read a JSONL file and yield parsed records."""
    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON on line {line_num}: {e}")


def read_csv(input_file):
    """Read a CSV file and yield records as dicts."""
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, 1):
            # Normalise common column names to canonical keys
            prompt = row.get("prompt", row.get("text", row.get("content", ""))).strip()
            if not prompt:
                print(f"Warning: Skipping row {row_num} with empty prompt")
                continue

            record = {"prompt": prompt}

            # Carry over expected / label / pii columns
            for key in ("expected", "label", "target", "pii"):
                val = row.get(key, "").strip()
                if val:
                    record["expected"] = val
                    break

            # Carry over original_label if present
            if "original_label" in row:
                record["original_label"] = row["original_label"].strip()

            yield record


def detect_format(file_path):
    """Detect the input file format from its extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".jsonl":
        return "jsonl"
    elif ext in (".csv", ".tsv"):
        return "csv"
    # Fall back to content sniffing
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    if first_line.startswith("{") and first_line.endswith("}"):
        return "jsonl"
    return "csv"


def convert_dataset(input_file, output_file, output_format="jsonl"):
    """
    Convert the input dataset to the evaluator-compatible format.

    Args:
        input_file:    Path to the input file (CSV or JSONL).
        output_file:   Path to the output file.
        output_format: "jsonl" (default) or "pipe" (legacy).
    """
    fmt = detect_format(input_file)
    print(f"Reading {input_file} as {fmt} format...")

    reader = read_jsonl(input_file) if fmt == "jsonl" else read_csv(input_file)

    converted = 0
    skipped = 0

    with open(output_file, "w", encoding="utf-8") as out:
        for record in reader:
            prompt = record.get("prompt", "").strip()
            if not prompt:
                skipped += 1
                continue

            expected = resolve_expected(record)
            if expected is None:
                print(f"Warning: Skipping record with unresolvable expected value: "
                      f"{prompt[:80]}...")
                skipped += 1
                continue

            if output_format == "pipe":
                escaped = prompt.replace('"', '""')
                out.write(f'"{escaped}"|{expected}\n')
            else:
                # JSONL output – preserve metadata if available
                out_record = {
                    "prompt": prompt,
                    "expected": expected,
                }
                metadata = record.get("metadata")
                if isinstance(metadata, dict) and metadata:
                    out_record["metadata"] = metadata
                json.dump(out_record, out, ensure_ascii=False)
                out.write("\n")

            converted += 1

    print(f"Conversion complete: {converted} records written, {skipped} skipped.")
    print(f"Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert datasets to the format required by the prompt evaluator."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to the input dataset file (CSV or JSONL).",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Path for the output file. Defaults to datasets/<input_name>_converted.<ext>.",
    )
    parser.add_argument(
        "--output-format", choices=["jsonl", "pipe"], default="jsonl",
        help="Output format (default: jsonl). Use 'pipe' for legacy pipe-delimited.",
    )

    args = parser.parse_args()

    # Resolve output path
    if args.output:
        output_file = args.output
    else:
        datasets_dir = "datasets"
        os.makedirs(datasets_dir, exist_ok=True)
        stem = Path(args.input).stem
        ext = "jsonl" if args.output_format == "jsonl" else "txt"
        output_file = os.path.join(datasets_dir, f"{stem}_converted.{ext}")

    convert_dataset(args.input, output_file, args.output_format)


if __name__ == "__main__":
    main()
