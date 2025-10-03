#!/usr/bin/env python3
"""
Evaluate existing scan results without re-scanning
"""

import csv
import argparse

def evaluate_existing_results(csv_file):
    """Evaluate accuracy from existing CSV results."""
    
    # Read the scanned results
    scan_results = []
    with open(csv_file, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 3:
                prompt = parts[0]
                expected = parts[1].strip('"').lower()
                outcome = parts[2].strip().lower()
                scan_results.append({
                    'prompt': prompt,
                    'expected': expected,
                    'outcome': outcome
                })
    
    print(f"Loaded {len(scan_results)} results from {csv_file}")
    
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
                      help='Input CSV file containing scan results to evaluate')
    
    args = parser.parse_args()
    evaluate_existing_results(args.input)

if __name__ == "__main__":
    main()
