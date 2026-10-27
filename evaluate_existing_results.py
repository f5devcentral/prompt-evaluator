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
"""
Evaluate existing scan results without re-scanning
"""

import argparse
from evaluation_common import calculate_metrics, format_metrics, read_results

def evaluate_existing_results(results_file):
    """Read historical/new result formats and return the same metrics used online.

    Malformed JSONL and unknown outcomes remain visible invalid exclusions. This
    operation never reads API credentials or rescans inputs.
    """
    records = read_results(results_file)
    metrics = calculate_metrics(records)
    print(f"Loaded {len(records)} results from {results_file}")
    print(format_metrics(metrics))
    return metrics

def main():
    parser = argparse.ArgumentParser(description='Evaluate existing scan results')
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Input file containing scan results (supports .jsonl, .csv, .tsv, .parquet)')
    
    args = parser.parse_args()
    evaluate_existing_results(args.input)

if __name__ == "__main__":
    main()
