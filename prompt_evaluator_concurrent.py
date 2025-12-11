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
Concurrent Prompt Evaluator

This script evaluates the accuracy of CalypsoAI scanners using concurrent API requests
to simulate real-world multi-user scenarios. It provides enhanced metrics for:
- Throughput (prompts/second)
- Latency distributions (p50, p95, p99)
- API behavior under load
- Comparison with sequential baseline
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import numpy as np

# Load environment variables
load_dotenv()
load_dotenv(override=True)

# Set up API variables
base_url = urljoin(os.environ.get("CALYPSOAI_URL", "https://www.us1.calypsoai.app"), "/backend/v1")

# Get the API key from environment
try:
    api_key = os.environ["CALYPSOAI_TOKEN"]
except KeyError:
    api_key = os.getenv("CALYPSOAI_TOKEN")
    if not api_key:
        raise ValueError("CALYPSOAI_TOKEN environment variable not found")

# Import the enhanced dataset reader
from tools.enhanced_dataset_reader import load_dataset_enhanced


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
                f.write("prompt,expected,outcome,response_time,prompt_size,original_line,metadata,queue_time_ms,request_time_ms,total_time_ms,worker_id,timestamp\n")
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prompt', 'expected', 'outcome', 'response_time', 'prompt_size', 'original_line', 
                         'metadata', 'queue_time_ms', 'request_time_ms', 'total_time_ms', 'worker_id', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in data:
                csv_record = {
                    'prompt': record.get('prompt', ''),
                    'expected': record.get('expected', ''),
                    'outcome': record.get('outcome', ''),
                    'response_time': record.get('response_time', ''),
                    'prompt_size': record.get('prompt_size', ''),
                    'original_line': record.get('original_line', ''),
                    'metadata': json.dumps(record.get('metadata', {})),
                    'queue_time_ms': record.get('queue_time_ms', ''),
                    'request_time_ms': record.get('request_time_ms', ''),
                    'total_time_ms': record.get('total_time_ms', ''),
                    'worker_id': record.get('worker_id', ''),
                    'timestamp': record.get('timestamp', '')
                }
                writer.writerow(csv_record)
    
    elif format_type == 'tsv':
        # Write as TSV
        if not data:
            with open(file_path, 'w') as f:
                f.write("prompt\texpected\toutcome\tresponse_time\tprompt_size\toriginal_line\tmetadata\tqueue_time_ms\trequest_time_ms\ttotal_time_ms\tworker_id\ttimestamp\n")
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write("prompt\texpected\toutcome\tresponse_time\tprompt_size\toriginal_line\tmetadata\tqueue_time_ms\trequest_time_ms\ttotal_time_ms\tworker_id\ttimestamp\n")
            
            for record in data:
                def escape_tsv(value):
                    if value is None:
                        return ''
                    return str(value).replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
                
                f.write(f"{escape_tsv(record.get('prompt', ''))}\t")
                f.write(f"{escape_tsv(record.get('expected', ''))}\t")
                f.write(f"{escape_tsv(record.get('outcome', ''))}\t")
                f.write(f"{escape_tsv(record.get('response_time', ''))}\t")
                f.write(f"{escape_tsv(record.get('prompt_size', ''))}\t")
                f.write(f"{escape_tsv(record.get('original_line', ''))}\t")
                f.write(f"{escape_tsv(json.dumps(record.get('metadata', {})))}\t")
                f.write(f"{escape_tsv(record.get('queue_time_ms', ''))}\t")
                f.write(f"{escape_tsv(record.get('request_time_ms', ''))}\t")
                f.write(f"{escape_tsv(record.get('total_time_ms', ''))}\t")
                f.write(f"{escape_tsv(record.get('worker_id', ''))}\t")
                f.write(f"{escape_tsv(record.get('timestamp', ''))}\n")
    
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
            dataset = load_dataset_enhanced(input_file, max_lines, format_hint)
            print(f"Loaded {len(dataset)} lines from {input_file}")
            return dataset
        except FileNotFoundError:
            error_msg = f"Error: Input file '{input_file}' not found. Please check the file path and try again."
            print(error_msg)
            return []
        except Exception as e:
            error_msg = f"Error reading file '{input_file}': {str(e)}"
            print(error_msg)
            return []
    
    def post(self, shared, prep_res, exec_res):
        shared["dataset"] = exec_res
        return "default"


# Concurrent node to scan multiple prompts in parallel
class ConcurrentScanPromptsNode(Node):
    """Scans multiple prompts concurrently using ThreadPoolExecutor."""
    
    def __init__(self, concurrency=10, rate_limit=None):
        super().__init__()
        self.concurrency = concurrency
        self.rate_limit = rate_limit
        self.progress_lock = Lock()
        self.completed = 0
        self.total = 0
        self.start_time = None
        
        # Configure session with connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=concurrency,
            pool_maxsize=concurrency * 2,
            max_retries=3
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
    
    def scan_prompt_with_timing(self, item, worker_id):
        """Scan a single prompt and track timing metrics."""
        prompt = item["prompt"]
        
        # Record when this request starts
        submit_time = time.time()
        queue_start = submit_time - self.start_time
        
        try:
            # Record start of actual API request
            request_start = time.time()
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
            payload = {"input": prompt}
            url = f"{base_url}/scans"
            
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Calculate timing
            request_time = time.time() - request_start
            total_time = time.time() - submit_time
            queue_time = request_start - submit_time
            
            outcome = response.json()
            
            # Handle the API response format
            if 'result' in outcome and 'outcome' in outcome['result']:
                result_outcome = outcome['result']['outcome']
            else:
                result_outcome = outcome.get('result', {}).get('outcome', 'no_result')
            
            # Update progress
            with self.progress_lock:
                self.completed += 1
                if self.completed % 10 == 0 or self.completed == self.total:
                    elapsed = time.time() - self.start_time
                    throughput = self.completed / elapsed if elapsed > 0 else 0
                    print(f"Progress: {self.completed}/{self.total} ({self.completed/self.total*100:.1f}%) - Throughput: {throughput:.2f} prompts/sec")
            
            return {
                "prompt": prompt,
                "expected": item["expected"],
                "outcome": result_outcome,
                "response_time": request_time,
                "prompt_size": len(prompt),
                "original_line": item["original_line"],
                "queue_time_ms": queue_time * 1000,
                "request_time_ms": request_time * 1000,
                "total_time_ms": total_time * 1000,
                "worker_id": worker_id,
                "timestamp": datetime.fromtimestamp(request_start).isoformat()
            }
        except Exception as e:
            # Update progress even on error
            with self.progress_lock:
                self.completed += 1
                if self.completed % 10 == 0 or self.completed == self.total:
                    print(f"Progress: {self.completed}/{self.total} ({self.completed/self.total*100:.1f}%)")
            
            return {
                "prompt": prompt,
                "expected": item["expected"],
                "outcome": f"error: {str(e)}",
                "response_time": None,
                "prompt_size": len(prompt),
                "original_line": item["original_line"],
                "queue_time_ms": None,
                "request_time_ms": None,
                "total_time_ms": None,
                "worker_id": worker_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def prep(self, shared):
        dataset = shared["dataset"]
        self.total = len(dataset)
        
        if self.total == 0:
            print("\nNo prompts to scan. The dataset is empty.")
            return []
        
        print(f"\nStarting concurrent scan of {self.total} prompts with {self.concurrency} workers...")
        return dataset
    
    def exec(self, dataset):
        if not dataset:
            return []
        
        results = []
        self.start_time = time.time()
        worker_counter = 0
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all tasks
            future_to_item = {}
            for item in dataset:
                worker_id = worker_counter % self.concurrency
                future = executor.submit(self.scan_prompt_with_timing, item, worker_id)
                future_to_item[future] = item
                worker_counter += 1
                
                # Rate limiting if specified
                if self.rate_limit:
                    time.sleep(1.0 / self.rate_limit)
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                result = future.result()
                results.append(result)
        
        total_elapsed = time.time() - self.start_time
        print(f"\nCompleted scanning {len(results)} prompts in {total_elapsed:.2f} seconds")
        print(f"Overall throughput: {len(results)/total_elapsed:.2f} prompts/sec")
        
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
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        output_file = shared.get("output_file", "scanned_output.csv")
        results_format = shared.get("results_format", "json")
        
        # Create results directory
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Extract dataset name from input file
        dataset_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Determine file extension based on format
        extension_map = {
            'json': 'jsonl',
            'csv': 'csv',
            'tsv': 'tsv',
            'parquet': 'parquet'
        }
        extension = extension_map.get(results_format, 'jsonl')
        
        # Create main results filename with _concurrent suffix
        main_results_file = os.path.join(results_dir, f"{dataset_name}_concurrent_results.{extension}")
        return main_results_file, shared["scan_results"], results_format
    
    def exec(self, inputs):
        output_file, scan_results, results_format = inputs
        
        if not scan_results:
            print(f"No results to save to {output_file}.")
            write_results_to_file([], output_file, results_format)
            return output_file
        
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
        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
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
        
        # Extract timing data
        request_times = [r.get('request_time_ms') for r in scan_results if r.get('request_time_ms') is not None]
        queue_times = [r.get('queue_time_ms') for r in scan_results if r.get('queue_time_ms') is not None]
        total_times = [r.get('total_time_ms') for r in scan_results if r.get('total_time_ms') is not None]
        
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
Overall: {throughput:.2f} prompts/sec

Request Latency (API call time):
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
        scan_results, fp_file, fn_file, output_format = inputs
        
        if not scan_results:
            return fp_file, fn_file, 0, 0
        
        false_positives = []
        false_negatives = []
        
        for result in scan_results:
            expected = result.get("expected", "").lower()
            outcome = result.get("outcome", "").lower()
            
            if expected == 'false' and outcome == 'flagged':
                false_positives.append(result)
            elif expected == 'true' and outcome == 'cleared':
                false_negatives.append(result)
        
        # Write files
        write_results_to_file(false_positives, fp_file, output_format)
        write_results_to_file(false_negatives, fn_file, output_format)
        
        return fp_file, fn_file, len(false_positives), len(false_negatives)
    
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
        if results['total'] == 0:
            return "\nEvaluation Results:\n------------------\nNo data was processed. No results to display."
        
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
    
    args = parser.parse_args()
    
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
    
    try:
        flow.run(shared)
        
        if "dataset" in shared and not shared["dataset"]:
            print("\nNo data was processed. Exiting.")
            return
        
        print(f"\nResults have been saved to: {shared.get('output_file', 'results/')}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
