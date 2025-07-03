#!/usr/bin/env python3
"""
Prompt Injection Evaluator (Prompts API)

This script evaluates the accuracy of CalypsoAI scanners using the /prompts API endpoint.
It follows the project's design patterns:
- Workflow: Breaking down the task into logical steps
- Batch: Processing multiple prompts efficiently
- Structured Output: Ensuring consistent output format

The /prompts endpoint provides more detailed information including LLM responses and scanner results.
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

# Utility function to send a prompt using CalypsoAI /prompts endpoint
def calypsoai_prompt(prompt, project=None, provider=None, verbose=False):
    """Send a prompt using the CalypsoAI /prompts API endpoint."""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        "input": prompt,
        "verbose": verbose
    }
    
    # Add optional parameters if provided
    if project:
        payload["project"] = project
    if provider:
        payload["provider"] = provider
    
    url = f"{base_url}/prompts"
    
    # Record start time
    start_time = time.time()
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    outcome = response.json()
    result = outcome.get('result', {})
    
    return {
        'outcome': result.get('outcome', 'no_result'),
        'response': result.get('response', ''),
        'scanner_results': result.get('scannerResults', []),
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

# Batch node to send multiple prompts
class SendPromptsNode(BatchNode):
    """Sends multiple prompts using the CalypsoAI /prompts API endpoint."""
    
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
            print("\nNo prompts to send. The dataset is empty.")
            return []
            
        print(f"\nStarting to send {self.total_prompts} prompts...")
        return dataset
    
    def exec(self, item):
        prompt = item["prompt"]
        try:
            result = calypsoai_prompt(prompt, verbose=True)
            outcome = result['outcome']
            response = result['response']
            scanner_results = result['scanner_results']
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
                print(f"Progress: {self.processed_count}/{self.total_prompts} prompts sent ({(self.processed_count/self.total_prompts*100):.1f}%)")
            
            return {
                "prompt": prompt,
                "expected": item["expected"],
                "outcome": outcome,
                "response": response,
                "scanner_results": scanner_results,
                "response_time": response_time,
                "prompt_size": prompt_size,
                "original_line": item["original_line"]
            }
        except Exception as e:
            print(f"Error processing prompt: {str(e)}")
            return {
                "prompt": prompt,
                "expected": item["expected"],
                "outcome": "error",
                "response": "",
                "scanner_results": [],
                "response_time": 0,
                "prompt_size": len(prompt),
                "original_line": item["original_line"],
                "error": str(e)
            }
    
    def post(self, shared, prep_res, exec_res_list):
        shared["prompt_results"] = exec_res_list
        shared["response_times"] = self.response_times
        shared["prompt_sizes"] = self.prompt_sizes
        return "default"

# Node to save results to CSV
class SaveResultsNode(Node):
    """Saves the prompt results to a CSV file."""
    
    def prep(self, shared):
        output_file = shared.get("output_file", "prompts_results.csv")
        prompt_results = shared.get("prompt_results", [])
        return output_file, prompt_results
    
    def exec(self, inputs):
        output_file, prompt_results = inputs
        
        if not prompt_results:
            print("No results to save.")
            return
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'prompt', 'expected', 'outcome', 'response', 
                    'response_time', 'prompt_size', 'scanner_results', 'original_line'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in prompt_results:
                    # Convert scanner_results to string for CSV
                    scanner_results_str = str(result.get('scanner_results', []))
                    
                    writer.writerow({
                        'prompt': result.get('prompt', ''),
                        'expected': result.get('expected', ''),
                        'outcome': result.get('outcome', ''),
                        'response': result.get('response', ''),
                        'response_time': result.get('response_time', 0),
                        'prompt_size': result.get('prompt_size', 0),
                        'scanner_results': scanner_results_str,
                        'original_line': result.get('original_line', '')
                    })
            
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")
    
    def post(self, shared, prep_res, exec_res):
        return "default"

# Node to evaluate accuracy
class EvaluateAccuracyNode(Node):
    """Evaluates the accuracy of the prompt outcomes against expected results."""
    
    def prep(self, shared):
        return shared["prompt_results"]
    
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
                "f1_score": 0,
                "outcome_distribution": {},
                "error_count": 0
            }
        
        # Initialize counters
        true_positive = 0
        true_negative = 0
        false_positive = 0
        false_negative = 0
        outcome_distribution = {}
        error_count = 0
        
        for result in scan_results:
            expected = result.get('expected', '').lower()
            actual = result.get('outcome', '').lower()
            
            # Count outcomes
            outcome_distribution[actual] = outcome_distribution.get(actual, 0) + 1
            
            # Check for errors
            if actual == 'error':
                error_count += 1
                continue
            
            # Determine if prediction is correct based on expected vs actual
            # For prompt injection evaluation, we typically expect:
            # - "true", "injection", "malicious", "attack" expected outcomes should be flagged/blocked
            # - "false", "benign", "safe", "normal" expected outcomes should be cleared
            
            # Normalize expected values
            if expected in ['true', 'injection', 'malicious', 'attack']:
                expected_normalized = 'true'
            elif expected in ['false', 'benign', 'safe', 'normal']:
                expected_normalized = 'false'
            else:
                expected_normalized = expected
            
            # Normalize actual values
            if actual in ['flagged', 'blocked']:
                actual_normalized = 'flagged'
            elif actual == 'cleared':
                actual_normalized = 'cleared'
            else:
                actual_normalized = actual
            
            # Check conditions for confusion matrix
            if expected_normalized == 'true' and actual_normalized == 'flagged':
                true_positive += 1
            elif expected_normalized == 'false' and actual_normalized == 'cleared':
                true_negative += 1
            elif expected_normalized == 'false' and actual_normalized == 'flagged':
                false_positive += 1
            elif expected_normalized == 'true' and actual_normalized == 'cleared':
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
        
        return {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "total": total,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "outcome_distribution": outcome_distribution,
            "error_count": error_count
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
Errors: {results['error_count']}

Outcome Distribution:
"""
        for outcome, count in results['outcome_distribution'].items():
            percentage = (count / results['total']) * 100 if results['total'] > 0 else 0
            output += f"  {outcome}: {count} ({percentage:.1f}%)\n"
        
        return output
    
    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"

# Node to calculate latency statistics
class LatencyStatsNode(Node):
    """Calculates and displays latency statistics from the prompt results."""
    
    def prep(self, shared):
        response_times = shared.get("response_times", [])
        prompt_sizes = shared.get("prompt_sizes", [])
        prompt_results = shared.get("prompt_results", [])
        return response_times, prompt_sizes, prompt_results
    
    def exec(self, inputs):
        response_times, prompt_sizes, prompt_results = inputs
        
        if not response_times or not prompt_sizes:
            return "No response time or prompt size data available. No prompts were processed."
        
        # Filter out None values
        valid_data = [(t, s, r) for t, s, r in zip(response_times, prompt_sizes, prompt_results) if t is not None]
        
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
    """Creates the evaluation workflow."""
    # Create nodes
    load_dataset = LoadDatasetNode()
    send_prompts = SendPromptsNode()
    save_results = SaveResultsNode()
    evaluate_accuracy = EvaluateAccuracyNode()
    display_results = DisplayResultsNode()
    latency_stats = LatencyStatsNode()
    
    # Connect nodes in sequence
    load_dataset >> send_prompts >> save_results >> evaluate_accuracy >> display_results >> latency_stats
    
    # Create flow with the starting node
    return Flow(start=load_dataset)

def main():
    """Main function to run the prompt evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate CalypsoAI scanners using the /prompts API endpoint")
    parser.add_argument("--input", "-i", default="prompt_inject_dataset.csv", 
                       help="Input CSV file containing prompts (default: prompt_inject_dataset.csv)")
    parser.add_argument("--output", "-o", default="prompts_results.csv", 
                       help="Output CSV file for results (default: prompts_results.csv)")
    parser.add_argument("--max-lines", "-m", type=int, 
                       help="Maximum number of lines to process")
    
    args = parser.parse_args()
    
    # Create and run the flow
    flow = create_evaluation_flow()
    
    shared_data = {
        "input_file": args.input,
        "output_file": args.output,
        "max_lines": args.max_lines
    }
    
    print("Starting Prompt Evaluation (Prompts API)")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    if args.max_lines:
        print(f"Max lines: {args.max_lines}")
    
    try:
        flow.run(shared_data)
        print("\nEvaluation completed successfully!")
    except Exception as e:
        print(f"\nError during evaluation: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 