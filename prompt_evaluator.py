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





# Utility function to scan a prompt using CalypsoAI
import os
import time
import argparse
from pocketflow import Node, BatchNode, Flow
from calypsoai_client import send_request
from evaluation_common import add_api_arguments, calculate_metrics, error_result, false_results, format_latency, format_metrics, latency_statistics, record_category, request_options, result_path, sample_record, write_results_to_file, dataset_inputs, load_dataset_inputs

def calypsoai_scan(prompt, project=None, verbose=False, diagnostics=False,
                   timeout=None, config=None):
    """Scan string input with flagOnly enabled and a bounded request timeout."""
    return send_request("scans", prompt, project=project, verbose=verbose,
                        diagnostics=diagnostics, timeout=timeout, config=config)




# Node to load the dataset
class LoadDatasetNode(Node):
    """Loads the prompt injection dataset from various file formats."""
    
    def prep(self, shared):
        """Preflight input/output paths before any API or output side effects."""
        return dataset_inputs(shared, "json", "")
    
    def exec(self, inputs):
        """Fail unreadable/empty inputs before the save/export workflow can run."""
        return load_dataset_inputs(inputs)
    
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
    
    def prep(self, shared):
        """Reset run state and resolve config only when there are inputs."""
        dataset = shared["dataset"]
        self.total_prompts = len(dataset)
        self.processed_count = 0
        self.response_times = []
        self.prompt_sizes = []
        self.start_time = time.time()
        self._options = request_options(shared, prompts=False) if dataset else {}
        return dataset
    
    def exec(self, item):
        """Preserve provenance and safe failure categories for each input."""
        try:
            row = sample_record(item, calypsoai_scan(item["prompt"], **getattr(self, "_options", {})))
            if record_category(row) in ("tp", "tn", "fp", "fn"):
                self.response_times.append(row["response_time"])
                self.prompt_sizes.append(row["prompt_size"])
            return row
        except Exception as error:
            return error_result(item, error)
        finally:
            self.processed_count += 1
            if self.processed_count % 10 == 0 or self.processed_count == self.total_prompts:
                print(f"Progress: {self.processed_count}/{self.total_prompts} prompts processed")
    
    def post(self, shared, prep_res, exec_res_list):
        shared["scan_results"] = exec_res_list
        shared["response_times"] = self.response_times
        shared["prompt_sizes"] = self.prompt_sizes
        shared["total_scan_time"] = time.time() - self.start_time
        return "default"

# Node to save scan results
class SaveResultsNode(Node):
    """Saves the scan results to a file in the results folder."""
    
    def prep(self, shared):
        """Resolve the selected format and an output confined to results/."""
        format_type = shared.get("results_format", "json")
        path = result_path(shared["input_file"], format_type,
                           shared.get("output_file"), suffix="")
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
        """Export the same rows classified as errors in the confusion matrix."""
        records, output_file, format_type = inputs
        rows = false_results(records)[0]
        write_results_to_file(rows, output_file, format_type)
        return output_file
    
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
        """Export the same rows classified as errors in the confusion matrix."""
        records, output_file, format_type = inputs
        rows = false_results(records)[1]
        write_results_to_file(rows, output_file, format_type)
        return output_file
    
    def post(self, shared, prep_res, exec_res):
        shared["false_negatives_file"] = exec_res
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

# Node to calculate and display latency statistics
class LatencyStatsNode(Node):
    """Calculates and displays latency statistics from the scan results."""
    
    def prep(self, shared):
        return shared.get("scan_results", []), shared.get("total_scan_time")
    
    def exec(self, inputs):
        """Report aggregate latency without logging prompt text."""
        return format_latency(*inputs)
    
    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"

# Node to generate PDF report
class GeneratePDFReportNode(Node):
    """Generates a PDF report from evaluation results."""
    
    def prep(self, shared):
        return shared
    
    def exec(self, shared):
        """Build a PDF from exactly the rows and exclusions used online."""
        if shared.get("skip_pdf", False):
            return None
        try:
            from report_generator import PDFReportGenerator
            rows = shared.get("scan_results", [])
            fps, fns = false_results(rows)
            return PDFReportGenerator().generate_report(
                dataset_name=os.path.splitext(os.path.basename(shared["output_file"]))[0].removesuffix("_results"),
                metrics=shared["evaluation_results"],
                false_positives=fps, false_negatives=fns,
                latency_stats=latency_statistics(rows, shared.get("total_scan_time")),
                evaluation_mode="scans",
            )
        except Exception as error:
            print(f"Warning: PDF generation failed ({type(error).__name__})")
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
                      help='Input dataset containing prompts to evaluate')
    parser.add_argument('--lines', '-l', type=int, default=None,
                      help='Number of lines to process from the input file (optional)')
    parser.add_argument('--output', '-o', type=str, default=None,
                      help='Output filename within results/ (default: dataset-derived)')
    parser.add_argument('--format', '-f', type=str, default='json', 
                      choices=['json', 'csv', 'tsv', 'parquet'],
                      help='Output format for false positives/negatives (default: json)')
    parser.add_argument('--results-format', '-r', type=str, default='json',
                      choices=['json', 'csv', 'tsv', 'parquet'],
                      help='Output format for main results file (default: json/jsonl)')
    
    add_api_arguments(parser, prompts=False)
    args = parser.parse_args()
    
    # Create and run the evaluation flow
    flow = create_evaluation_flow()
    
    # Set up shared data with command line arguments
    shared = {
        "input_file": args.input,
        "max_lines": args.lines,
        "output_file": args.output,
        "output_format": args.format,
        "results_format": args.results_format
    }
    
    shared.update(vars(args))
    try:
        result_path(args.input, args.results_format, args.output)
        # Run the flow
        flow.run(shared)
        
        # Check if the dataset is empty
        if "dataset" in shared and not shared["dataset"]:
            print("\nNo data was processed. Exiting.")
            return
        
        print(f"\nResults have been saved to: {shared.get('output_file', args.output)}")
        return 2 if shared.get("evaluation_results", {}).get("excluded_count", 0) else 0
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
