#!/usr/bin/env python3
"""
Prompt Injection Evaluator

This example demonstrates how to evaluate the accuracy of a any CalypsoAI scanners
using the CalypsoAI API. It follows the project's design patterns:
- Workflow: Breaking down the task into logical steps
- Batch: Processing multiple prompts efficiently
- Structured Output: Ensuring consistent output format
"""

import os
import csv
import requests
import time
import argparse
from urllib.parse import urljoin
from dotenv import load_dotenv
from pocketflow import Node, BatchNode, Flow

# Load environment variables
load_dotenv()
load_dotenv(override=True)

# Set up API variables
base_url = urljoin(os.environ.get("CALYPSOAI_URL", "https://calypsoai.app"), "/backend/v1")
api_key = os.environ["CALYPSOAI_TOKEN"]

# Utility function to scan a prompt using CalypsoAI
def calypsoai_scan(prompt):
    """Scan a prompt using the CalypsoAI API."""
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
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    outcome = response.json()
    return {
        'outcome': outcome.get('result', {}).get('outcome', 'no_result'),
        'response_time': elapsed_time
    }

# Node to load the dataset
class LoadDatasetNode(Node):
    """Loads the prompt injection dataset from a CSV file."""
    
    def prep(self, shared):
        input_file = shared.get("input_file", "prompt_inject_dataset.csv")
        max_lines = shared.get("max_lines", None)
        return input_file, max_lines
    
    def exec(self, inputs):
        input_file, max_lines = inputs
        dataset = []
        line_count = 0
        
        try:
            with open(input_file, 'r') as infile:
                for line in infile:
                    # Check if we've reached the maximum number of lines
                    if max_lines is not None and line_count >= max_lines:
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Split line by | and strip surrounding quotation marks
                    parts = line.split('|')
                    if len(parts) < 2:
                        continue
                    
                    prompt = parts[0].strip().strip('"').strip("'")
                    expected = parts[1].strip().lower() if len(parts) > 1 else "unknown"
                    
                    dataset.append({
                        "prompt": prompt,
                        "expected": expected,
                        "original_line": line
                    })
                    
                    line_count += 1
            
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
    
    def prep(self, shared):
        dataset = shared["dataset"]
        self.total_prompts = len(dataset)
        
        if self.total_prompts == 0:
            print("\nNo prompts to scan. The dataset is empty.")
            return []
            
        print(f"\nStarting scan of {self.total_prompts} prompts...")
        return dataset
    
    def exec(self, item):
        prompt = item["prompt"]
        try:
            result = calypsoai_scan(prompt)
            outcome = result['outcome']
            response_time = result['response_time']
            
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
                "response_time": None,
                "prompt_size": len(prompt),
                "original_line": item["original_line"]
            }
    
    def post(self, shared, prep_res, exec_res_list):
        shared["scan_results"] = exec_res_list
        shared["response_times"] = self.response_times
        shared["prompt_sizes"] = self.prompt_sizes
        print(f"Completed scanning {len(exec_res_list)} prompts.")
        return "default"

# Node to save scan results
class SaveResultsNode(Node):
    """Saves the scan results to a CSV file."""
    
    def prep(self, shared):
        output_file = shared.get("output_file", "scanned_output.csv")
        return output_file, shared["scan_results"]
    
    def exec(self, inputs):
        output_file, scan_results = inputs
        
        if not scan_results:
            print(f"No results to save to {output_file}.")
            # Create an empty file with a header
            with open(output_file, 'w') as outfile:
                outfile.write("prompt|expected|outcome|response_time|prompt_size\n")
            return output_file
        
        with open(output_file, 'w') as outfile:
            for result in scan_results:
                response_time = result.get('response_time')
                response_time_str = f"{response_time:.4f}" if response_time is not None else "N/A"
                prompt_size = result.get('prompt_size', 'N/A')
                outfile.write(f"{result['original_line']}|{result['outcome']}|{response_time_str}|{prompt_size}\n")
        
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
        return response_times, prompt_sizes, scan_results
    
    def exec(self, inputs):
        response_times, prompt_sizes, scan_results = inputs
        
        if not response_times or not prompt_sizes:
            return "No response time or prompt size data available. No prompts were processed."
        
        # Filter out None values
        valid_data = [(t, s, r) for t, s, r in zip(response_times, prompt_sizes, scan_results) if t is not None]
        
        if not valid_data:
            return "No valid response time data available. No prompts were successfully processed."
        
        # Unzip the valid data
        valid_times, valid_sizes, valid_results = zip(*valid_data)
        
        # Calculate response time statistics
        avg_time = sum(valid_times) / len(valid_times)
        min_time = min(valid_times)
        max_time = max(valid_times)
        
        # Find the prompts with min and max response times
        min_time_idx = valid_times.index(min_time)
        max_time_idx = valid_times.index(max_time)
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
Latency Statistics:
------------------
Average Response Time: {avg_time:.4f} seconds
Minimum Response Time: {min_time:.4f} seconds (Prompt Size: {min_time_size} chars)
Maximum Response Time: {max_time:.4f} seconds (Prompt Size: {max_time_size} chars)
Total Requests: {len(valid_times)}/{len(response_times)} valid responses

Prompt Size Statistics:
---------------------
Average Prompt Size: {avg_size:.1f} characters
Minimum Prompt Size: {min_size} characters
Maximum Prompt Size: {max_size} characters

Sample Prompts:
--------------
Fastest Response ({min_time:.4f}s):
"{min_time_prompt[:100]}{'...' if len(min_time_prompt) > 100 else ''}"

Slowest Response ({max_time:.4f}s):
"{max_time_prompt[:100]}{'...' if len(max_time_prompt) > 100 else ''}"
"""
        return output
    
    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"

def create_evaluation_flow():
    """Creates and returns the prompt injection evaluation flow."""
    # Create nodes
    load_dataset = LoadDatasetNode()
    scan_prompts = ScanPromptsNode()
    save_results = SaveResultsNode()
    evaluate_accuracy = EvaluateAccuracyNode()
    display_results = DisplayResultsNode()
    latency_stats = LatencyStatsNode()
    
    # Connect nodes in sequence
    load_dataset >> scan_prompts >> save_results >> evaluate_accuracy >> display_results >> latency_stats
    
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
    
    args = parser.parse_args()
    
    # Create and run the evaluation flow
    flow = create_evaluation_flow()
    
    # Set up shared data with command line arguments
    shared = {
        "input_file": args.input,
        "max_lines": args.lines,
        "output_file": args.output
    }
    
    try:
        # Run the flow
        flow.run(shared)
        
        # Check if the dataset is empty
        if "dataset" in shared and not shared["dataset"]:
            print("\nNo data was processed. Exiting.")
            return
        
        print(f"\nResults have been saved to: {args.output}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return

if __name__ == "__main__":
    main() 