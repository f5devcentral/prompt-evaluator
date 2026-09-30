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
Prompt Injection Evaluator

This example demonstrates how to evaluate the accuracy of any CalypsoAI scanners
using the CalypsoAI API. It follows the project's design patterns:
- Workflow: Breaking down the task into logical steps
- Batch: Processing multiple prompts efficiently
- Structured Output: Ensuring consistent output format
"""

import os
import csv
import json
import requests
import time
import argparse
from datetime import datetime
from urllib.parse import urljoin
from dotenv import load_dotenv
from pocketflow import Node, BatchNode, Flow
import numpy as np

# Load environment variables
load_dotenv()
load_dotenv(override=True)

# Set up API variables
base_url = urljoin(os.environ.get("CALYPSOAI_URL", "https://www.us1.calypsoai.app"), "/backend/v1")

# Get the API key from environment
try:
    # Try direct environment access
    api_key = os.environ["CALYPSOAI_TOKEN"]
except KeyError:
    # Try getenv as fallback
    api_key = os.getenv("CALYPSOAI_TOKEN")
    
    if not api_key:
        raise ValueError("CALYPSOAI_TOKEN environment variable not found")

# ---------------------------------------------------------------------------
# Scanner name resolution
# ---------------------------------------------------------------------------
# Scan responses identify scanners by opaque ID only. The /scanners endpoint
# exposes the ID -> name mapping, but it is partitioned by "source", so the
# full map is assembled by querying each known source once and caching the
# merged result for the lifetime of the process.
SCANNER_SOURCES = ("vendor", "system", "zip", "share", "internal")
SCANNER_REQUEST_TIMEOUT = 30
SCANNER_PAGE_LIMIT = 100

# Cache sentinel. None means "never fetched"; a dict means "already fetched",
# including an empty dict, which records a failed lookup so the API is not
# re-queried once per prompt for the rest of the run.
_scanner_map_cache = None


def fetch_scanner_map(force_refresh=False):
    """Build a mapping of scanner ID to human-readable scanner name.

    The mapping is cached at module level because it is identical for every
    prompt in a run; without caching this would cost one request per source
    per prompt.

    Args:
        force_refresh (bool): Ignore any cached map and re-query the API.

    Returns:
        dict: {scanner_id: scanner_name}. Empty when every source failed,
        which callers treat as "fall back to raw IDs" rather than fatal.

    Edge cases:
        - A failing source is warned about and skipped, so one bad source does
          not discard scanners successfully read from the others.
        - A total failure is cached as {} so the lookup is attempted only once.
        - This is deliberately lazy. Calling it at import time would fire HTTP
          requests simply by importing the module, which breaks CI and --help.
    """
    global _scanner_map_cache

    if _scanner_map_cache is not None and not force_refresh:
        return _scanner_map_cache

    scanner_map = {}

    with requests.Session() as session:
        session.headers.update({'Authorization': f'Bearer {api_key}'})
        for source in SCANNER_SOURCES:
            try:
                response = session.get(
                    f"{base_url}/scanners",
                    params={'source': source, 'limit': SCANNER_PAGE_LIMIT},
                    timeout=SCANNER_REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as e:
                print(f"Warning: could not fetch scanners for source '{source}': {e}")
                continue

            for scanner in payload.get("scanners", []) or []:
                scanner_id = scanner.get("id")
                if scanner_id:
                    scanner_map[scanner_id] = scanner.get("name") or scanner_id

    if not scanner_map:
        print("Warning: scanner name lookup returned no scanners; "
              "results will report raw scanner IDs.")

    _scanner_map_cache = scanner_map
    return scanner_map


def extract_triggered_scanners(result_payload, scanner_map=None):
    """Return the names of the scanners that did not pass for a single scan.

    Args:
        result_payload (dict): The 'result' object from a /scans response.
        scanner_map (dict): Optional {id: name} mapping from
            fetch_scanner_map(). When omitted, or when an ID is missing from
            it, the raw scanner ID is used so the information is preserved
            rather than replaced by a placeholder.

    Returns:
        list[str]: Triggered scanner names (or IDs), in API order.

    Edge cases:
        - Missing or non-list 'scannerResults' yields an empty list.
        - Non-dict entries are skipped defensively.
        - Entries with no 'outcome' count as triggered, since a result we
          cannot classify is worth surfacing rather than silently dropping.
    """
    scanner_map = scanner_map or {}
    scanner_results = result_payload.get('scannerResults') or []

    if not isinstance(scanner_results, list):
        return []

    triggered = []
    for scanner in scanner_results:
        if not isinstance(scanner, dict):
            continue
        if str(scanner.get('outcome', '')).lower() == 'passed':
            continue
        scanner_id = scanner.get('scannerId')
        if scanner_id is None:
            continue
        triggered.append(scanner_map.get(scanner_id, scanner_id))

    return triggered


# Utility function to scan a prompt using CalypsoAI
def calypsoai_scan(prompt, scanner_map=None):
    """Scan a prompt using the CalypsoAI API.

    Args:
        prompt (str): The prompt text to scan.
        scanner_map (dict): Optional {scanner_id: name} mapping used to label
            the scanners that flagged the prompt. Raw IDs are reported when
            this is absent.

    Returns:
        dict: 'outcome' (str), 'response_time' (float seconds) and 'scanners'
        (list of triggered scanner names).
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        "input": prompt
    }
    url = f"{base_url}/scans"
    
    # Record start time
    start_time = time.time()
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    # Debug: Print response details
    # print(f"\n--- Response Details ---")
    # print(f"Status Code: {response.status_code}")
    # print(f"Response Headers: {dict(response.headers)}")
    # try:
    #     print(f"Response Body: {response.text}")
    # except:
    #     print("Could not print response body")
    # print("------------------------\n")
    
    response.raise_for_status()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    outcome = response.json()
    
    # Handle the new API response format
    # The response now has: { "result": { "outcome": "flagged" } }
    result = outcome.get('result') or {}
    if not isinstance(result, dict):
        result = {}
    result_outcome = result.get('outcome', 'no_result')
    
    return {
        'outcome': result_outcome,
        'response_time': elapsed_time,
        'scanners': extract_triggered_scanners(result, scanner_map)
    }

# Import the enhanced dataset reader
from tools.enhanced_dataset_reader import load_dataset_enhanced


def _format_scanners(value):
    """Flatten a scanners list into one delimited cell for flat text formats.

    CSV and TSV cannot hold a list, so the names are joined with '; '. JSON and
    Parquet keep the native list instead.

    Args:
        value: The record's 'scanners' entry; normally a list, possibly None.

    Returns:
        str: Delimited scanner names, or '' when there are none.
    """
    if isinstance(value, (list, tuple)):
        return '; '.join(str(v) for v in value)
    return '' if value is None else str(value)


def write_results_to_file(data, file_path, format_type):
    """Write results to file in the specified format."""
    import os
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if format_type == 'json':
        # Write as JSONL
        with open(file_path, 'w') as f:
            for record in data:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
    
    elif format_type == 'csv':
        # Write as CSV
        if not data:
            with open(file_path, 'w') as f:
                f.write("prompt,expected,outcome,scanners,response_time,prompt_size,original_line,metadata\n")
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prompt', 'expected', 'outcome', 'scanners', 'response_time', 'prompt_size', 'original_line', 'metadata']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in data:
                # Flatten metadata for CSV
                csv_record = {
                    'prompt': record.get('prompt', ''),
                    'expected': record.get('expected', ''),
                    'outcome': record.get('outcome', ''),
                    'scanners': _format_scanners(record.get('scanners')),
                    'response_time': record.get('response_time', ''),
                    'prompt_size': record.get('prompt_size', ''),
                    'original_line': record.get('original_line', ''),
                    'metadata': json.dumps(record.get('metadata', {}))
                }
                writer.writerow(csv_record)
    
    elif format_type == 'tsv':
        # Write as TSV
        if not data:
            with open(file_path, 'w') as f:
                f.write("prompt\texpected\toutcome\tscanners\tresponse_time\tprompt_size\toriginal_line\tmetadata\n")
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            # Write header
            f.write("prompt\texpected\toutcome\tscanners\tresponse_time\tprompt_size\toriginal_line\tmetadata\n")
            
            for record in data:
                # Escape tabs in data
                def escape_tsv(value):
                    if value is None:
                        return ''
                    return str(value).replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
                
                f.write(f"{escape_tsv(record.get('prompt', ''))}\t")
                f.write(f"{escape_tsv(record.get('expected', ''))}\t")
                f.write(f"{escape_tsv(record.get('outcome', ''))}\t")
                f.write(f"{escape_tsv(_format_scanners(record.get('scanners')))}\t")
                f.write(f"{escape_tsv(record.get('response_time', ''))}\t")
                f.write(f"{escape_tsv(record.get('prompt_size', ''))}\t")
                f.write(f"{escape_tsv(record.get('original_line', ''))}\t")
                f.write(f"{escape_tsv(json.dumps(record.get('metadata', {})))}\n")
    
    elif format_type == 'parquet':
        # Write as Parquet
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_parquet(file_path, index=False)
        except ImportError:
            print("Warning: pandas not available for parquet export. Falling back to JSON.")
            write_results_to_file(data, file_path.replace('.parquet', '.jsonl'), 'json')

# Node to load the dataset
class LoadDatasetNode(Node):
    """Loads the prompt injection dataset from various file formats."""
    
    def prep(self, shared):
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        max_lines = shared.get("max_lines", None)
        format_hint = shared.get("format_hint", None)
        return input_file, max_lines, format_hint
    
    def exec(self, inputs):
        input_file, max_lines, format_hint = inputs
        
        try:
            # Use the enhanced dataset reader
            dataset = load_dataset_enhanced(input_file, max_lines, format_hint)
            print(f"Loaded {len(dataset)} lines from {input_file}")
            return dataset
        except FileNotFoundError:
            error_msg = f"Error: Input file '{input_file}' not found. Please check the file path and try again."
            print(error_msg)
            # Return an empty dataset to allow the flow to continue
            return []
        except Exception as e:
            error_msg = f"Error reading file '{input_file}': {str(e)}"
            print(error_msg)
            # Return an empty dataset to allow the flow to continue
            return []
    
    def post(self, shared, prep_res, exec_res):
        shared["dataset"] = exec_res
        return "default"

# Batch node to scan multiple prompts
class ScanPromptsNode(BatchNode):
    """Scans multiple prompts using the CalypsoAI API."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_count = 0
        self.total_prompts = 0
        self.response_times = []
        self.prompt_sizes = []
        self.start_time = None
        # Resolved once in prep() so the lookup cost is paid per run, not per prompt.
        self.scanner_map = {}
    
    def prep(self, shared):
        dataset = shared["dataset"]
        self.total_prompts = len(dataset)
        
        if self.total_prompts == 0:
            print("\nNo prompts to scan. The dataset is empty.")
            return []

        # Resolve scanner IDs to names once up front. Opt-out avoids the extra
        # requests when only pass/fail outcomes are needed.
        if shared.get("resolve_scanner_names", True):
            self.scanner_map = fetch_scanner_map()
        else:
            self.scanner_map = {}

        print(f"\nStarting scan of {self.total_prompts} prompts...")
        self.start_time = time.time()
        return dataset
    
    def exec(self, item):
        prompt = item["prompt"]
        try:
            result = calypsoai_scan(prompt, self.scanner_map)
            outcome = result['outcome']
            response_time = result['response_time']
            scanners = result['scanners']
            
            # Calculate prompt size (in characters)
            prompt_size = len(prompt)
            
            # Store response time and prompt size for later analysis
            self.response_times.append(response_time)
            self.prompt_sizes.append(prompt_size)
            
            # Update the processed count
            self.processed_count += 1
            # Print progress every 10 items or at the end
            if self.processed_count % 10 == 0 or self.processed_count == self.total_prompts:
                print(f"Progress: {self.processed_count}/{self.total_prompts} prompts scanned ({(self.processed_count/self.total_prompts*100):.1f}%)")
            
            return {
                "prompt": prompt,
                "expected": item["expected"],
                "outcome": outcome,
                "scanners": scanners,
                "response_time": response_time,
                "prompt_size": prompt_size,
                "original_line": item["original_line"]
            }
        except Exception as e:
            # Update the processed count even for errors
            self.processed_count += 1
            # Print progress every 10 items or at the end
            if self.processed_count % 10 == 0 or self.processed_count == self.total_prompts:
                print(f"Progress: {self.processed_count}/{self.total_prompts} prompts scanned ({(self.processed_count/self.total_prompts*100):.1f}%)")
            
            return {
                "prompt": prompt,
                "expected": item["expected"],
                "outcome": f"error: {str(e)}",
                "scanners": [],
                "response_time": None,
                "prompt_size": len(prompt),
                "original_line": item["original_line"]
            }
    
    def post(self, shared, prep_res, exec_res_list):
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        shared["scan_results"] = exec_res_list
        shared["response_times"] = self.response_times
        shared["prompt_sizes"] = self.prompt_sizes
        shared["total_scan_time"] = elapsed_time
        print(f"Completed scanning {len(exec_res_list)} prompts in {elapsed_time:.2f} seconds.")
        # print(f"DEBUG: ScanPromptsNode stored {len(exec_res_list)} results in shared data")
        # if exec_res_list:
        #     print(f"DEBUG: First scan result: {exec_res_list[0]}")
        return "default"

# Node to save scan results
class SaveResultsNode(Node):
    """Saves the scan results to a file in the results folder."""
    
    def prep(self, shared):
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        output_file = shared.get("output_file", "scanned_output.csv")
        results_format = shared.get("results_format", "json")  # Default to JSONL
        
        # Create results directory
        import os
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Extract dataset name from input file
        dataset_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Determine file extension based on format
        if results_format == 'json':
            extension = 'jsonl'
        elif results_format == 'csv':
            extension = 'csv'
        elif results_format == 'tsv':
            extension = 'tsv'
        elif results_format == 'parquet':
            extension = 'parquet'
        else:
            extension = 'jsonl'  # Default fallback
        
        # Create main results filename in results folder
        main_results_file = os.path.join(results_dir, f"{dataset_name}_results.{extension}")
        return main_results_file, shared["scan_results"], results_format
    
    def exec(self, inputs):
        output_file, scan_results, results_format = inputs
        
        if not scan_results:
            print(f"No results to save to {output_file}.")
            # Create an empty file with proper headers
            write_results_to_file([], output_file, results_format)
            return output_file
        
        # Use the write_results_to_file function with the specified format
        write_results_to_file(scan_results, output_file, results_format)
        
        return output_file
    
    def post(self, shared, prep_res, exec_res):
        shared["output_file"] = exec_res
        return "default"

# Node to evaluate scanner accuracy
class EvaluateAccuracyNode(Node):
    """Evaluates the accuracy of the prompt injection scanner."""
    
    def prep(self, shared):
        return shared["scan_results"]
    
    def exec(self, scan_results):
        # print(f"DEBUG: EvaluateAccuracyNode received {len(scan_results) if scan_results else 0} scan results")
        # if scan_results:
        #     print(f"DEBUG: First result: {scan_results[0]}")
        
        # Check if there are any results to evaluate
        if not scan_results:
            print("No results to evaluate.")
            return {
                "true_positive": 0,
                "true_negative": 0,
                "false_positive": 0,
                "false_negative": 0,
                "total": 0,
                "accuracy": 0,
                "precision": 0,
                "recall": 0,
                "f1_score": 0
            }
            
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
        
        # Return structured results
        return {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "total": total,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["evaluation_results"] = exec_res
        return "default"

# Node to export false positives
class ExportFalsePositivesNode(Node):
    """Exports prompts that were marked as false positives to a JSON file."""
    
    def prep(self, shared):
        scan_results = shared.get("scan_results", [])
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        output_file = shared.get("output_file", "scanned_output.csv")
        output_format = shared.get("output_format", "json")
        
        # Create results directory
        import os
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Extract dataset name from input file
        dataset_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Create false positives filename in results folder with appropriate extension
        if output_format == 'json':
            extension = 'jsonl'
        elif output_format == 'csv':
            extension = 'csv'
        elif output_format == 'tsv':
            extension = 'tsv'
        elif output_format == 'parquet':
            extension = 'parquet'
        else:
            extension = 'jsonl'  # Default fallback
        
        false_positives_file = os.path.join(results_dir, f"{dataset_name}_false_positives.{extension}")
        return scan_results, false_positives_file, output_format
    
    def exec(self, inputs):
        scan_results, false_positives_file, output_format = inputs
        
        if not scan_results:
            print("No results to export for false positives.")
            return false_positives_file
        
        false_positives = []
        for result in scan_results:
            expected = result.get("expected", "").lower()
            outcome = result.get("outcome", "").lower()
            
            # False positive: expected 'false' but got 'flagged'
            if expected == 'false' and outcome == 'flagged':
                # Create structured record
                json_record = {
                    "prompt": result['prompt'],
                    "expected": result['expected'],
                    "outcome": result['outcome'],
                    "scanners": result.get('scanners', []),
                    "response_time": result.get('response_time'),
                    "prompt_size": result.get('prompt_size'),
                    "original_line": result.get('original_line', ''),
                    "metadata": {
                        "type": "false_positive",
                        "export_timestamp": datetime.now().isoformat()
                    }
                }
                false_positives.append(json_record)
        
        if not false_positives:
            print("No false positives found to export.")
            # Create empty file
            write_results_to_file([], false_positives_file, output_format)
            return false_positives_file
        
        # Write false positives using the specified format
        write_results_to_file(false_positives, false_positives_file, output_format)
        
        print(f"Exported {len(false_positives)} false positives to {false_positives_file}")
        return false_positives_file
    
    def post(self, shared, prep_res, exec_res):
        shared["false_positives_file"] = exec_res
        return "default"

# Node to export false negatives
class ExportFalseNegativesNode(Node):
    """Exports prompts that were marked as false negatives to a JSON file."""
    
    def prep(self, shared):
        scan_results = shared.get("scan_results", [])
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        output_file = shared.get("output_file", "scanned_output.csv")
        output_format = shared.get("output_format", "json")
        
        # Create results directory
        import os
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Extract dataset name from input file
        dataset_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Create false negatives filename in results folder with appropriate extension
        if output_format == 'json':
            extension = 'jsonl'
        elif output_format == 'csv':
            extension = 'csv'
        elif output_format == 'tsv':
            extension = 'tsv'
        elif output_format == 'parquet':
            extension = 'parquet'
        else:
            extension = 'jsonl'  # Default fallback
        
        false_negatives_file = os.path.join(results_dir, f"{dataset_name}_false_negatives.{extension}")
        return scan_results, false_negatives_file, output_format
    
    def exec(self, inputs):
        scan_results, false_negatives_file, output_format = inputs
        
        if not scan_results:
            print("No results to export for false negatives.")
            return false_negatives_file
        
        false_negatives = []
        for result in scan_results:
            expected = result.get("expected", "").lower()
            outcome = result.get("outcome", "").lower()
            
            # False negative: expected 'true' but got 'cleared'
            if expected == 'true' and outcome == 'cleared':
                # Create structured record
                json_record = {
                    "prompt": result['prompt'],
                    "expected": result['expected'],
                    "outcome": result['outcome'],
                    "scanners": result.get('scanners', []),
                    "response_time": result.get('response_time'),
                    "prompt_size": result.get('prompt_size'),
                    "original_line": result.get('original_line', ''),
                    "metadata": {
                        "type": "false_negative",
                        "export_timestamp": datetime.now().isoformat()
                    }
                }
                false_negatives.append(json_record)
        
        if not false_negatives:
            print("No false negatives found to export.")
            # Create empty file
            write_results_to_file([], false_negatives_file, output_format)
            return false_negatives_file
        
        # Write false negatives using the specified format
        write_results_to_file(false_negatives, false_negatives_file, output_format)
        
        print(f"Exported {len(false_negatives)} false negatives to {false_negatives_file}")
        return false_negatives_file
    
    def post(self, shared, prep_res, exec_res):
        shared["false_negatives_file"] = exec_res
        return "default"

# Node to display results
class DisplayResultsNode(Node):
    """Displays the evaluation results."""
    
    def prep(self, shared):
        return shared["evaluation_results"]
    
    def exec(self, results):
        # Check if there are any results to display
        if results['total'] == 0:
            output = """
Evaluation Results:
------------------
No data was processed. No results to display.
"""
            return output
            
        # Format results for display
        output = f"""
Evaluation Results:
------------------
True Positives: {results['true_positive']}
True Negatives: {results['true_negative']}
False Positives: {results['false_positive']}
False Negatives: {results['false_negative']}
Total Samples: {results['total']}
Overall Accuracy: {results['accuracy']:.2%}
Precision: {results['precision']:.2%}
Recall: {results['recall']:.2%}
F1 Score: {results['f1_score']:.2%}
"""
        return output
    
    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"

# Node to calculate and display latency statistics
class LatencyStatsNode(Node):
    """Calculates and displays latency statistics from the scan results."""
    
    def prep(self, shared):
        response_times = shared.get("response_times", [])
        prompt_sizes = shared.get("prompt_sizes", [])
        scan_results = shared.get("scan_results", [])
        total_scan_time = shared.get("total_scan_time", 0)
        return response_times, prompt_sizes, scan_results, total_scan_time
    
    def exec(self, inputs):
        response_times, prompt_sizes, scan_results, total_scan_time = inputs
        
        if not response_times or not prompt_sizes:
            return "No response time or prompt size data available. No prompts were processed."
        
        # Filter out None values
        valid_data = [(t, s, r) for t, s, r in zip(response_times, prompt_sizes, scan_results) if t is not None]
        
        if not valid_data:
            return "No valid response time data available. No prompts were successfully processed."
        
        # Unzip the valid data
        valid_times, valid_sizes, valid_results = zip(*valid_data)
        
        # Convert to milliseconds for consistency with concurrent evaluator
        valid_times_ms = [t * 1000 for t in valid_times]
        
        # Calculate response time statistics
        avg_time = np.mean(valid_times_ms)
        min_time = np.min(valid_times_ms)
        max_time = np.max(valid_times_ms)
        
        # Calculate percentiles
        p50 = np.percentile(valid_times_ms, 50)
        p95 = np.percentile(valid_times_ms, 95)
        p99 = np.percentile(valid_times_ms, 99)
        
        # Calculate throughput
        throughput = len(scan_results) / total_scan_time if total_scan_time > 0 else 0
        
        # Find the prompts with min and max response times
        min_time_idx = valid_times_ms.index(min_time)
        max_time_idx = valid_times_ms.index(max_time)
        min_time_prompt = valid_results[min_time_idx]["prompt"]
        max_time_prompt = valid_results[max_time_idx]["prompt"]
        min_time_size = valid_sizes[min_time_idx]
        max_time_size = valid_sizes[max_time_idx]
        
        # Calculate prompt size statistics
        avg_size = sum(valid_sizes) / len(valid_sizes)
        min_size = min(valid_sizes)
        max_size = max(valid_sizes)
        
        # Format the output
        output = f"""
Performance Metrics:
===================

Throughput:
-----------
Overall: {throughput:.2f} prompts/sec
Total Prompts: {len(scan_results)}
Total Elapsed Time: {total_scan_time:.2f} seconds

Request Latency (API call time):
--------------------------------
Average: {avg_time:.2f} ms
Minimum: {min_time:.2f} ms
Maximum: {max_time:.2f} ms
p50 (median): {p50:.2f} ms
p95: {p95:.2f} ms
p99: {p99:.2f} ms
Total Requests: {len(valid_times)}/{len(response_times)} valid responses

Prompt Size Statistics:
----------------------
Average Prompt Size: {avg_size:.1f} characters
Minimum Prompt Size: {min_size} characters
Maximum Prompt Size: {max_size} characters

Sample Prompts:
--------------
Fastest Response ({min_time:.2f}ms):
"{min_time_prompt[:100]}{'...' if len(min_time_prompt) > 100 else ''}"

Slowest Response ({max_time:.2f}ms):
"{max_time_prompt[:100]}{'...' if len(max_time_prompt) > 100 else ''}"
"""
        return output
    
    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"

# Node to generate PDF report
class GeneratePDFReportNode(Node):
    """Generates a PDF report from evaluation results."""
    
    def prep(self, shared):
        # Check if PDF generation dependencies are available
        try:
            import reportlab
        except ImportError:
            return None, None, None, None
        
        evaluation_results = shared.get("evaluation_results", {})
        scan_results = shared.get("scan_results", [])
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        total_scan_time = shared.get("total_scan_time", 0)
        
        # Extract dataset name from input file
        dataset_name = os.path.splitext(os.path.basename(input_file))[0]
        
        return evaluation_results, dataset_name, scan_results, total_scan_time
    
    def exec(self, inputs):
        evaluation_results, dataset_name, scan_results, total_scan_time = inputs
        
        # Skip if dependencies not available
        if evaluation_results is None:
            return None
        
        try:
            from report_generator import PDFReportGenerator
            
            # Prepare metrics
            metrics = {
                'true_positive': evaluation_results.get('true_positive', 0),
                'true_negative': evaluation_results.get('true_negative', 0),
                'false_positive': evaluation_results.get('false_positive', 0),
                'false_negative': evaluation_results.get('false_negative', 0),
                'total': evaluation_results.get('total', 0),
                'accuracy': evaluation_results.get('accuracy', 0),
                'precision': evaluation_results.get('precision', 0),
                'recall': evaluation_results.get('recall', 0),
                'f1_score': evaluation_results.get('f1_score', 0)
            }
            
            # Extract false positives and false negatives from scan results
            false_positives = []
            false_negatives = []
            
            for result in scan_results:
                expected = result.get("expected", "").lower()
                outcome = result.get("outcome", "").lower()
                
                if expected == 'false' and outcome == 'flagged':
                    false_positives.append(result)
                elif expected == 'true' and outcome == 'cleared':
                    false_negatives.append(result)
            
            # Calculate enhanced latency statistics with percentiles
            response_times = [r.get('response_time') for r in scan_results if r.get('response_time') is not None]
            latency_stats = None
            
            if response_times:
                # Convert to milliseconds for consistency
                response_times_ms = [t * 1000 for t in response_times]
                
                latency_stats = {
                    'average_latency': np.mean(response_times_ms) / 1000,  # Keep in seconds for PDF compatibility
                    'min_latency': np.min(response_times_ms) / 1000,
                    'max_latency': np.max(response_times_ms) / 1000,
                    'p50_latency': np.percentile(response_times_ms, 50) / 1000,
                    'p95_latency': np.percentile(response_times_ms, 95) / 1000,
                    'p99_latency': np.percentile(response_times_ms, 99) / 1000,
                    'throughput': len(scan_results) / total_scan_time if total_scan_time > 0 else 0,
                    'total_time': total_scan_time,
                    'total_prompts': len(scan_results)
                }
            
            # Generate report
            generator = PDFReportGenerator()
            output_path = generator.generate_report(
                dataset_name=dataset_name,
                metrics=metrics,
                false_positives=false_positives if false_positives else None,
                false_negatives=false_negatives if false_negatives else None,
                latency_stats=latency_stats
            )
            
            return output_path
        except Exception as e:
            print(f"Warning: Could not generate PDF report: {str(e)}")
            return None
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared["pdf_report_path"] = exec_res
            print(f"\nPDF Report: {exec_res}")
        return "default"

def create_evaluation_flow():
    """Creates and returns the prompt injection evaluation flow."""
    # Create nodes
    load_dataset = LoadDatasetNode()
    scan_prompts = ScanPromptsNode()
    save_results = SaveResultsNode()
    evaluate_accuracy = EvaluateAccuracyNode()
    export_false_positives = ExportFalsePositivesNode()
    export_false_negatives = ExportFalseNegativesNode()
    display_results = DisplayResultsNode()
    latency_stats = LatencyStatsNode()
    generate_pdf_report = GeneratePDFReportNode()
    
    # Connect nodes in sequence
    load_dataset >> scan_prompts >> save_results >> evaluate_accuracy >> export_false_positives >> export_false_negatives >> display_results >> latency_stats >> generate_pdf_report
    
    # Create flow starting with load_dataset node
    return Flow(start=load_dataset)

def main():
    parser = argparse.ArgumentParser(description='Evaluate prompts using CalypsoAI API')
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Input CSV file containing prompts to evaluate')
    parser.add_argument('--lines', '-l', type=int, default=None,
                      help='Number of lines to process from the input file (optional)')
    parser.add_argument('--output', '-o', type=str, default='scanned_output.csv',
                      help='Output file name for results (default: scanned_output.csv)')
    parser.add_argument('--format', '-f', type=str, default='json', 
                      choices=['json', 'csv', 'tsv', 'parquet'],
                      help='Output format for false positives/negatives (default: json)')
    parser.add_argument('--results-format', '-r', type=str, default='json',
                      choices=['json', 'csv', 'tsv', 'parquet'],
                      help='Output format for main results file (default: json/jsonl)')
    parser.add_argument('--no-scanner-names', action='store_true',
                      help='Skip the scanner ID to name lookup and report raw '
                           'scanner IDs instead (saves a few startup requests)')
    
    args = parser.parse_args()
    
    # Create and run the evaluation flow
    flow = create_evaluation_flow()
    
    # Set up shared data with command line arguments
    shared = {
        "input_file": args.input,
        "max_lines": args.lines,
        "output_file": args.output,
        "output_format": args.format,
        "results_format": args.results_format,
        "resolve_scanner_names": not args.no_scanner_names
    }
    
    try:
        # Run the flow
        flow.run(shared)
        
        # Check if the dataset is empty
        if "dataset" in shared and not shared["dataset"]:
            print("\nNo data was processed. Exiting.")
            return
        
        print(f"\nResults have been saved to: {shared.get('output_file', args.output)}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return

if __name__ == "__main__":
    main() 