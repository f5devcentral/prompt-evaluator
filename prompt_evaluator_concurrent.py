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
Concurrent Prompt Evaluator

This script evaluates the accuracy of CalypsoAI scanners using concurrent API requests
to simulate real-world multi-user scenarios. It provides enhanced metrics for:
- Throughput (prompts/second)
- Latency distributions (p50, p95, p99)
- API behavior under load
- Comparison with sequential baseline
"""









# Node to load the dataset
import os
import requests
import time
import argparse
from datetime import datetime
from pocketflow import Node, Flow
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import numpy as np
from calypsoai_client import send_request
from evaluation_common import record_category
from evaluation_common import add_api_arguments, calculate_metrics, error_result, false_results, format_metrics, request_options, result_path, sample_record, write_results_to_file, dataset_inputs, load_dataset_inputs

class LoadDatasetNode(Node):
    """Loads the prompt injection dataset from various file formats."""
    
    def prep(self, shared):
        """Preflight input/output paths before any API or output side effects."""
        return dataset_inputs(shared, "json", "_concurrent")
    
    def exec(self, inputs):
        """Fail unreadable/empty inputs before the save/export workflow can run."""
        return load_dataset_inputs(inputs)
    
    def post(self, shared, prep_res, exec_res):
        shared["dataset"] = exec_res
        return "default"


# Concurrent node to scan multiple prompts in parallel
class ConcurrentScanPromptsNode(Node):
    """Scans multiple prompts concurrently using ThreadPoolExecutor."""
    
    def __init__(self, concurrency=10, rate_limit=None):
        """Create bounded workers; invalid concurrency/rates fail before requests."""
        super().__init__()
        import math
        from threading import local
        if type(concurrency) is not int or concurrency <= 0:
            raise ValueError("Concurrency must be a positive integer")
        if rate_limit is not None and (not math.isfinite(rate_limit) or rate_limit <= 0):
            raise ValueError("Rate limit must be finite and positive")
        self.concurrency = concurrency
        self.rate_limit = rate_limit
        self.progress_lock = Lock()
        self.completed = 0
        self.total = 0
        self.start_time = None
        self._local = local()
        self._sessions = []
        self._options = {}

    @property
    def session(self):
        """Use one connection pool per thread; never replay non-idempotent POSTs."""
        if not hasattr(self._local, "session"):
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=0)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            self._local.session = session
            with self.progress_lock:
                self._local.worker_id = len(self._sessions)
                self._sessions.append(session)
        return self._local.session

    def scan_prompt_with_timing(self, item, worker_id, submitted_at=None):
        """Measure executor wait from submission, retaining row provenance on failure."""
        started = time.perf_counter()
        request_timestamp = datetime.now().astimezone().isoformat()
        submitted_at = started if submitted_at is None else submitted_at
        try:
            result = send_request("scans", item["prompt"], session=self.session, **self._options)
            row = sample_record(item, result)
        except Exception as error:
            row = error_result(item, error)
        row.update({
            "queue_time_ms": (started - submitted_at) * 1000,
            "request_time_ms": row["response_time"] * 1000 if row["response_time"] is not None else None,
            "total_time_ms": (time.perf_counter() - submitted_at) * 1000,
            "worker_id": getattr(self._local, "worker_id", worker_id),
            "request_timestamp": request_timestamp,
        })
        with self.progress_lock:
            self.completed += 1
            if self.completed % 10 == 0 or self.completed == self.total:
                print(f"Progress: {self.completed}/{self.total} prompts processed")
        return row
    
    def prep(self, shared):
        dataset = shared["dataset"]
        self.total = len(dataset)
        self.completed = 0
        self._options = request_options(shared) if dataset else {}
        return dataset
    
    def exec(self, dataset):
        """Collect out-of-order results and close every worker-local session."""
        if not dataset:
            return []
        self.start_time = time.time()
        results = []
        try:
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                futures = []
                for index, item in enumerate(dataset):
                    submitted_at = time.perf_counter()
                    futures.append(executor.submit(
                        self.scan_prompt_with_timing, item, index % self.concurrency, submitted_at
                    ))
                    if self.rate_limit:
                        time.sleep(1.0 / self.rate_limit)
                for future in as_completed(futures):
                    results.append(future.result())
        finally:
            for session in self._sessions:
                session.close()
            self._sessions.clear()
        return results
    
    def post(self, shared, prep_res, exec_res):
        shared["scan_results"] = exec_res
        shared["concurrent_metrics"] = {
            "total_time": time.time() - self.start_time if self.start_time else 0,
            "concurrency": self.concurrency,
            "rate_limit": self.rate_limit
        }
        return "default"


# Node to save scan results
class SaveResultsNode(Node):
    """Saves the scan results to a file in the results folder."""
    
    def prep(self, shared):
        """Resolve the selected format and an output confined to results/."""
        format_type = shared.get("results_format", "json")
        path = result_path(shared["input_file"], format_type,
                           shared.get("output_file"), suffix="_concurrent")
        return path, shared.get("scan_results", []), format_type
    
    def exec(self, inputs):
        """Serialize all fields, preserving nested evidence in tabular formats."""
        output_file, rows, format_type = inputs
        return write_results_to_file(rows, output_file, format_type)
    
    def post(self, shared, prep_res, exec_res):
        shared["output_file"] = exec_res
        return "default"


# Node to evaluate scanner accuracy
class EvaluateAccuracyNode(Node):
    """Evaluates the accuracy of the prompt injection scanner."""
    
    def prep(self, shared):
        return shared["scan_results"]
    
    def exec(self, scan_results):
        """Score rows using the shared detection and exclusion policy."""
        return calculate_metrics(scan_results)
    
    def post(self, shared, prep_res, exec_res):
        shared["evaluation_results"] = exec_res
        return "default"


# Node to calculate concurrent-specific metrics
class ConcurrentMetricsNode(Node):
    """Calculates and displays concurrent performance metrics."""
    
    def prep(self, shared):
        scan_results = shared.get("scan_results", [])
        concurrent_metrics = shared.get("concurrent_metrics", {})
        return scan_results, concurrent_metrics
    
    def exec(self, inputs):
        scan_results, concurrent_metrics = inputs
        
        if not scan_results:
            return "No results to analyze."
        
        # Match sequential/PDF latency membership; throughput still counts attempts.
        timed_results = [r for r in scan_results if record_category(r) in ("tp", "tn", "fp", "fn")]
        request_times = [r.get('request_time_ms') for r in timed_results if r.get('request_time_ms') is not None]
        queue_times = [r.get('queue_time_ms') for r in timed_results if r.get('queue_time_ms') is not None]
        total_times = [r.get('total_time_ms') for r in timed_results if r.get('total_time_ms') is not None]
        
        if not request_times:
            return "No valid timing data available."
        
        # Calculate percentiles
        def percentile(data, p):
            return np.percentile(data, p) if data else 0
        
        # Request time percentiles
        req_p50 = percentile(request_times, 50)
        req_p95 = percentile(request_times, 95)
        req_p99 = percentile(request_times, 99)
        req_avg = np.mean(request_times)
        req_min = np.min(request_times)
        req_max = np.max(request_times)
        
        # Queue time stats (time waiting for worker)
        queue_avg = np.mean(queue_times) if queue_times else 0
        queue_max = np.max(queue_times) if queue_times else 0
        
        # Total time stats
        total_avg = np.mean(total_times) if total_times else 0
        
        # Throughput
        total_time = concurrent_metrics.get('total_time', 0)
        throughput = len(scan_results) / total_time if total_time > 0 else 0
        
        # Concurrency info
        concurrency = concurrent_metrics.get('concurrency', 'N/A')
        rate_limit = concurrent_metrics.get('rate_limit', 'None')
        
        output = f"""
Concurrent Performance Metrics:
==============================

Configuration:
--------------
Concurrent Workers: {concurrency}
Rate Limit: {rate_limit} requests/sec
Total Prompts: {len(scan_results)}
Total Elapsed Time: {total_time:.2f} seconds

Throughput:
-----------
Attempt throughput: {throughput:.2f} prompts/sec

Request Latency (evaluable rows):
--------------------------------
Average: {req_avg:.2f} ms
Minimum: {req_min:.2f} ms
Maximum: {req_max:.2f} ms
p50 (median): {req_p50:.2f} ms
p95: {req_p95:.2f} ms
p99: {req_p99:.2f} ms

Queue Time (waiting for worker):
--------------------------------
Average: {queue_avg:.2f} ms
Maximum: {queue_max:.2f} ms

Total Time (queue + request):
-----------------------------
Average: {total_avg:.2f} ms
"""
        
        # Store metrics for potential report generation
        metrics_data = {
            'concurrency': concurrency,
            'rate_limit': rate_limit,
            'total_prompts': len(scan_results),
            'total_time': total_time,
            'throughput': throughput,
            'request_latency': {
                'avg': req_avg,
                'min': req_min,
                'max': req_max,
                'p50': req_p50,
                'p95': req_p95,
                'p99': req_p99
            },
            'queue_time': {
                'avg': queue_avg,
                'max': queue_max
            },
            'total_time_stats': {
                'avg': total_avg
            }
        }
        
        return output, metrics_data
    
    def post(self, shared, prep_res, exec_res):
        if isinstance(exec_res, tuple):
            output, metrics_data = exec_res
            shared["concurrent_performance"] = metrics_data
            print(output)
        else:
            print(exec_res)
        return "default"


# Node to export false positives/negatives
class ExportFalseResultsNode(Node):
    """Exports false positives and false negatives."""
    
    def prep(self, shared):
        scan_results = shared.get("scan_results", [])
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        output_format = shared.get("output_format", "json")
        
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        dataset_name = os.path.splitext(os.path.basename(input_file))[0]
        
        extension_map = {'json': 'jsonl', 'csv': 'csv', 'tsv': 'tsv', 'parquet': 'parquet'}
        extension = extension_map.get(output_format, 'jsonl')
        
        fp_file = os.path.join(results_dir, f"{dataset_name}_concurrent_false_positives.{extension}")
        fn_file = os.path.join(results_dir, f"{dataset_name}_concurrent_false_negatives.{extension}")
        
        return scan_results, fp_file, fn_file, output_format
    
    def exec(self, inputs):
        """Keep exports and metric membership consistent for every outcome."""
        records, fp_file, fn_file, format_type = inputs
        fps, fns = false_results(records)
        write_results_to_file(fps, fp_file, format_type)
        write_results_to_file(fns, fn_file, format_type)
        return fp_file, fn_file, len(fps), len(fns)
    
    def post(self, shared, prep_res, exec_res):
        fp_file, fn_file, fp_count, fn_count = exec_res
        
        if fp_count > 0:
            print(f"\nExported {fp_count} false positives to {fp_file}")
        if fn_count > 0:
            print(f"Exported {fn_count} false negatives to {fn_file}")
        
        return "default"


# Node to display results
class DisplayResultsNode(Node):
    """Displays the evaluation results."""
    
    def prep(self, shared):
        return shared["evaluation_results"]
    
    def exec(self, results):
        """Display attempted/evaluated counts, including all-error runs."""
        return format_metrics(results)
    
    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"


def create_concurrent_evaluation_flow(concurrency=10, rate_limit=None):
    """Creates and returns the concurrent prompt evaluation flow."""
    load_dataset = LoadDatasetNode()
    scan_prompts = ConcurrentScanPromptsNode(concurrency=concurrency, rate_limit=rate_limit)
    save_results = SaveResultsNode()
    evaluate_accuracy = EvaluateAccuracyNode()
    concurrent_metrics = ConcurrentMetricsNode()
    export_false_results = ExportFalseResultsNode()
    display_results = DisplayResultsNode()
    
    # Connect nodes in sequence
    load_dataset >> scan_prompts >> save_results >> evaluate_accuracy >> concurrent_metrics >> export_false_results >> display_results
    
    return Flow(start=load_dataset)


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate prompts using CalypsoAI API with concurrent requests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with 10 concurrent workers (default)
  python prompt_evaluator_concurrent.py -i datasets/pii_dataset.csv
  
  # Run with 20 concurrent workers
  python prompt_evaluator_concurrent.py -i datasets/pii_dataset.csv --concurrency 20
  
  # Run with rate limiting (50 requests/sec)
  python prompt_evaluator_concurrent.py -i datasets/pii_dataset.csv --rate-limit 50
  
  # Test with small dataset
  python prompt_evaluator_concurrent.py -i datasets/pii_dataset.csv -l 50 --concurrency 5
"""
    )
    
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Input file containing prompts to evaluate')
    parser.add_argument('--lines', '-l', type=int, default=None,
                      help='Number of lines to process from the input file (optional)')
    parser.add_argument('--concurrency', '-c', type=int, default=10,
                      help='Number of concurrent workers (default: 10)')
    parser.add_argument('--rate-limit', type=float, default=None,
                      help='Maximum requests per second (optional)')
    parser.add_argument('--format', '-f', type=str, default='json', 
                      choices=['json', 'csv', 'tsv', 'parquet'],
                      help='Output format for false positives/negatives (default: json)')
    parser.add_argument('--results-format', '-r', type=str, default='json',
                      choices=['json', 'csv', 'tsv', 'parquet'],
                      help='Output format for main results file (default: json/jsonl)')
    
    parser.add_argument("--output", "-o", default=None, help="Output filename within results/")
    add_api_arguments(parser, prompts=False)
    args = parser.parse_args()
    
    # Display infrastructure impact warning
    print("\n" + "="*80)
    print("⚠️  INFRASTRUCTURE IMPACT WARNING")
    print("="*80)
    print("\nRunning concurrent evaluation can trigger infrastructure auto-scaling and")
    print("may impact shared resources.\n")
    print("Before proceeding, please confirm you have:")
    print("\n  1. ✓ Checked with your platform/infrastructure team")
    print("     - Understood auto-scaling policies")
    print("     - Determined safe concurrency levels for your environment")
    print("     - Scheduled during maintenance windows if necessary")
    print("     - Obtained approval for load testing")
    print("\n  2. ✓ Started conservatively")
    print(f"     - Current concurrency: {args.concurrency} workers")
    if args.concurrency > 10:
        print("       ⚠️  WARNING: Consider starting with --concurrency 5 or lower")
    if args.lines:
        print(f"     - Limited to {args.lines} prompts")
    else:
        print("       ⚠️  WARNING: Processing entire dataset - consider using --lines to limit")
    if args.rate_limit:
        print(f"     - Rate limiting: {args.rate_limit} requests/sec")
    else:
        print("       ⚠️  WARNING: No rate limiting - consider using --rate-limit")
    print("\n  3. ✓ Avoided peak hours for high concurrency testing")
    print("\nNot following these guidelines could cause:")
    print("  • Unexpected cloud infrastructure costs")
    print("  • Service disruptions to other teams or applications")
    print("  • Cascading failures if auto-scaling can't keep up")
    print("\n" + "="*80)
    
    # Prompt user to continue
    try:
        response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\nExecution cancelled by user.")
            return
    except (KeyboardInterrupt, EOFError):
        print("\n\nExecution cancelled by user.")
        return
    
    print("\n" + "="*80)
    print("Starting concurrent evaluation...")
    print("="*80 + "\n")
    
    # Create and run the concurrent evaluation flow
    flow = create_concurrent_evaluation_flow(
        concurrency=args.concurrency,
        rate_limit=args.rate_limit
    )
    
    # Set up shared data
    shared = {
        "input_file": args.input,
        "max_lines": args.lines,
        "output_format": args.format,
        "results_format": args.results_format
    }
    
    shared.update(vars(args))
    shared["output_file"] = args.output
    try:
        result_path(args.input, args.results_format, args.output, suffix="_concurrent")
        flow.run(shared)
        
        if "dataset" in shared and not shared["dataset"]:
            print("\nNo data was processed. Exiting.")
            return
        
        print(f"\nResults have been saved to: {shared.get('output_file', 'results/')}")
        return 2 if shared.get("evaluation_results", {}).get("excluded_count", 0) else 0
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
