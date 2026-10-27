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
"""Validate local dependencies and optional datasets; network access is opt-in."""

import argparse
import contextlib
import io
import os
import sys
from importlib import metadata
from pathlib import Path

import requests
from calypsoai_client import APIConfig
from evaluation_common import normalize_expected


def check_python_version():
    """Require Python 3.11+, the version exercised by project CI."""
    passed = sys.version_info >= (3, 11)
    print("Python 3.11+: " + ("passed" if passed else "required"))
    return passed


def check_required_packages():
    """Verify core distributions without installing anything or requiring Parquet."""
    required = ("requests", "pocketflow", "python-dotenv", "datasets", "huggingface-hub",
                "pandas", "reportlab", "matplotlib", "numpy")
    missing = []
    for package in required:
        try:
            metadata.version(package)
        except metadata.PackageNotFoundError:
            missing.append(package)
    if missing:
        print("Missing packages: " + ", ".join(missing))
        print("Activate the project Conda environment, then install requirements.txt.")
        return False
    print("Required packages: passed (Parquet engine is optional)")
    return True


def check_environment_variables():
    """Validate lazy API configuration without printing secret values."""
    try:
        APIConfig.from_environment()
    except ValueError as error:
        print(f"API configuration: {error}")
        return False
    print("API configuration: passed")
    return True


def check_calypsoai_api():
    """Probe the documented scanner listing, not an assumed health route."""
    try:
        config = APIConfig.from_environment()
        response = requests.get(
            f"{config.base_url}/scanners", params={"limit": 1},
            headers=config.headers, timeout=config.timeout,
        )
        if response.status_code == 401:
            print("API check: authentication failed (HTTP 401)")
            return False
        if response.status_code == 403:
            print("API check: scanner-list permission denied (HTTP 403); this is not proof of an outage")
            return False
        if response.status_code != 200:
            print(f"API check: HTTP {response.status_code}")
            return False
        body = response.json()
        if not isinstance(body, dict) or not isinstance(body.get("scanners"), list):
            print("API check: unexpected scanner-list response format")
            return False
    except requests.Timeout:
        print("API check: request timed out")
        return False
    except requests.RequestException:
        print("API check: connectivity failed")
        return False
    except ValueError:
        print("API check: invalid configuration or response JSON")
        return False
    print("API check: scanner listing accessible")
    return True


def check_file_permissions():
    """Inspect the output directory's writability without creating test files."""
    target = Path("results") if Path("results").exists() else Path.cwd()
    passed = os.access(target, os.W_OK)
    print("Output permissions: " + ("passed" if passed else "not writable"))
    return passed


def check_dataset(dataset_path, format_hint=None):
    """Validate supported input formats and labels without echoing prompt content."""
    try:
        from tools.enhanced_dataset_reader import load_dataset_enhanced
        with contextlib.redirect_stdout(io.StringIO()):
            records = load_dataset_enhanced(dataset_path, format_hint=format_hint)
        if not records or any(
            not isinstance(row.get("prompt"), str) or not row["prompt"]
            or normalize_expected(row.get("expected")) is None
            for row in records
        ):
            print("Dataset check: empty dataset, invalid prompt, or invalid label")
            return False
    except Exception as error:
        print(f"Dataset check failed ({type(error).__name__})")
        return False
    print(f"Dataset check: {len(records)} usable records")
    return True


def main():
    """Run offline checks by default; --check-api explicitly enables one GET."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", "-d", help="Optional dataset path")
    parser.add_argument("--format-hint", choices=("jsonl", "csv", "tsv", "pipe", "parquet"))
    parser.add_argument("--check-api", action="store_true", help="Contact configured tenant using GET /scanners?limit=1")
    args = parser.parse_args()
    checks = [check_python_version(), check_required_packages(), check_file_permissions()]
    if args.dataset:
        checks.append(check_dataset(args.dataset, args.format_hint))
    if args.check_api:
        checks.append(check_calypsoai_api())
    else:
        print("API check skipped (offline default; use --check-api explicitly)")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
