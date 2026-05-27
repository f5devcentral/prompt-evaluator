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

import csv
import json
import argparse
import os

def evaluate_existing_results(results_file):
    """Evaluate accuracy from existing results file (supports JSONL, CSV, TSV, Parquet)."""
    
    # Detect file format
    file_ext = os.path.splitext(results_file)[1].lower()
    
    scan_results = []
    
    # Read based on file format
    if file_ext == '.jsonl' or file_ext == '.json':
        # Read JSONL format
        with open(results_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        scan_results.append({
                            'prompt': record.get('prompt', ''),
                            'expected': str(record.get('expected', '')).lower(),
                            'outcome': str(record.get('outcome', '')).lower()
                        })
                    except json.JSONDecodeError:
                        continue
    
    elif file_ext == '.csv':
        # Read CSV format
        with open(results_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scan_results.append({
                    'prompt': row.get('prompt', ''),
                    'expected': str(row.get('expected', '')).lower(),
                    'outcome': str(row.get('outcome', '')).lower()
                })
    
    elif file_ext == '.tsv':
        # Read TSV format
        with open(results_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                scan_results.append({
                    'prompt': row.get('prompt', ''),
                    'expected': str(row.get('expected', '')).lower(),
                    'outcome': str(row.get('outcome', '')).lower()
                })
    
    elif file_ext == '.parquet':
        # Read Parquet format
        try:
            import pandas as pd
            df = pd.read_parquet(results_file)
            for _, row in df.iterrows():
                scan_results.append({
                    'prompt': str(row.get('prompt', '')),
                    'expected': str(row.get('expected', '')).lower(),
                    'outcome': str(row.get('outcome', '')).lower()
                })
        except ImportError:
            print("Error: pandas is required to read parquet files. Install with: pip install pandas pyarrow")
            return
    
    else:
        print(f"Unsupported file format: {file_ext}")
        print("Supported formats: .jsonl, .csv, .tsv, .parquet")
        return
    
    print(f"Loaded {len(scan_results)} results from {results_file}")
    
    if not scan_results:
        print("No results to evaluate.")
        return
    
    # Initialize counters
    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0
    
    for result in scan_results:
        expected = result["expected"]
        outcome = result["outcome"].lower()
        
        # Check conditions
        if expected == 'true' and outcome == 'flagged':
            true_positive += 1
        elif expected == 'false' and outcome == 'cleared':
            true_negative += 1
        elif expected == 'false' and outcome == 'flagged':
            false_positive += 1
        elif expected == 'true' and outcome == 'cleared':
            false_negative += 1
    
    # Calculate metrics
    total = true_positive + true_negative + false_positive + false_negative
    accuracy = (true_positive + true_negative) / total if total > 0 else 0
    
    # Calculate precision (true positives / (true positives + false positives))
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    
    # Calculate recall (true positives / (true positives + false negatives))
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    
    # Calculate F1 score (2 * precision * recall / (precision + recall))
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Display results
    print(f"""
Evaluation Results:
------------------
True Positives: {true_positive}
True Negatives: {true_negative}
False Positives: {false_positive}
False Negatives: {false_negative}
Total Samples: {total}
Overall Accuracy: {accuracy:.2%}
Precision: {precision:.2%}
Recall: {recall:.2%}
F1 Score: {f1_score:.2%}
""")

def main():
    parser = argparse.ArgumentParser(description='Evaluate existing scan results')
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Input file containing scan results (supports .jsonl, .csv, .tsv, .parquet)')
    
    args = parser.parse_args()
    evaluate_existing_results(args.input)

if __name__ == "__main__":
    main()
