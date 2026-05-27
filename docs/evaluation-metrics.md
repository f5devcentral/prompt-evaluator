# Evaluation Metrics Guide

## Overview

This guide explains all the evaluation metrics used by the Prompt Evaluator tools to assess the performance of AI safety scanners. Understanding these metrics is crucial for interpreting evaluation results and making informed decisions about scanner performance.

## Confusion Matrix Components

Before diving into specific metrics, it's important to understand the four possible outcomes when evaluating a prompt scanner:

### True Positives (TP)
- **Definition**: Prompts that are correctly identified as malicious/unsafe
- **Condition**: Expected = `true`, Scanner Result = `flagged`
- **Example**: A prompt injection attempt that the scanner correctly flags as malicious

### True Negatives (TN)
- **Definition**: Prompts that are correctly identified as safe/benign
- **Condition**: Expected = `false`, Scanner Result = `cleared`
- **Example**: A normal, harmless prompt that the scanner correctly allows through

### False Positives (FP)
- **Definition**: Safe prompts that are incorrectly flagged as malicious
- **Condition**: Expected = `false`, Scanner Result = `flagged`
- **Example**: A legitimate business query that gets incorrectly blocked
- **Impact**: Can cause legitimate users to be blocked or frustrated

### False Negatives (FN)
- **Definition**: Malicious prompts that are incorrectly allowed through
- **Condition**: Expected = `true`, Scanner Result = `cleared`
- **Example**: A sophisticated prompt injection that bypasses detection
- **Impact**: Security risk - malicious content gets through

## Performance Metrics

### Accuracy
- **Formula**: `(TP + TN) / (TP + TN + FP + FN)`
- **Definition**: The proportion of all predictions that are correct
- **Range**: 0.0 to 1.0 (or 0% to 100%)
- **Interpretation**: 
  - 1.0 = Perfect classification
  - 0.5 = Random guessing performance
  - < 0.5 = Worse than random
- **When to Use**: Overall performance assessment when classes are balanced

**Example Calculation**:
```
TP = 80, TN = 85, FP = 15, FN = 20
Accuracy = (80 + 85) / (80 + 85 + 15 + 20) = 165/200 = 0.825 (82.5%)
```

### Precision
- **Formula**: `TP / (TP + FP)`
- **Definition**: Of all the prompts flagged as malicious, how many were actually malicious?
- **Range**: 0.0 to 1.0 (or 0% to 100%)
- **Interpretation**:
  - High precision = Few false positives
  - Low precision = Many safe prompts incorrectly blocked
- **When to Use**: Important when false positives are costly (e.g., blocking legitimate users)

**Example Calculation**:
```
TP = 80, FP = 15
Precision = 80 / (80 + 15) = 80/95 = 0.842 (84.2%)
```

### Recall (Sensitivity)
- **Formula**: `TP / (TP + FN)`
- **Definition**: Of all the actual malicious prompts, how many were correctly identified?
- **Range**: 0.0 to 1.0 (or 0% to 100%)
- **Interpretation**:
  - High recall = Few false negatives
  - Low recall = Many malicious prompts slip through
- **When to Use**: Critical for security applications where missing threats is dangerous

**Example Calculation**:
```
TP = 80, FN = 20
Recall = 80 / (80 + 20) = 80/100 = 0.800 (80.0%)
```

### F1 Score
- **Formula**: `2 × (Precision × Recall) / (Precision + Recall)`
- **Definition**: Harmonic mean of precision and recall
- **Range**: 0.0 to 1.0 (or 0% to 100%)
- **Interpretation**:
  - Balances precision and recall
  - 1.0 = Perfect precision and recall
  - 0.0 = Either precision or recall is 0
- **When to Use**: When you need a single metric that balances both false positives and false negatives

**Example Calculation**:
```
Precision = 0.842, Recall = 0.800
F1 Score = 2 × (0.842 × 0.800) / (0.842 + 0.800) = 2 × 0.674 / 1.642 = 0.821 (82.1%)
```

## Metric Trade-offs

Understanding the relationships between these metrics is crucial:

### Precision vs Recall Trade-off
- **High Precision, Low Recall**: Conservative scanner that rarely makes mistakes but misses many threats
- **Low Precision, High Recall**: Aggressive scanner that catches most threats but has many false alarms
- **Balanced**: F1 score helps find the sweet spot

### Choosing the Right Metric

**For Security-Focused Applications**:
- Prioritize **Recall** - better to have some false positives than miss real threats
- Monitor **F1 Score** for overall balance

**For User Experience-Focused Applications**:
- Prioritize **Precision** - avoid frustrating legitimate users with false blocks
- Monitor **Accuracy** for overall performance

**For General Assessment**:
- Use **F1 Score** as the primary metric
- Review individual **Precision** and **Recall** values

## Practical Examples

### Example 1: E-commerce Chatbot
```
Scenario: Customer service chatbot that needs to detect inappropriate content
Priority: User experience (avoid blocking legitimate customers)
Recommended Metrics: Focus on Precision, monitor F1 Score
```

### Example 2: Content Moderation API
```
Scenario: API that screens user-generated content for safety
Priority: Security (catch all harmful content)
Recommended Metrics: Focus on Recall, monitor Precision to avoid over-blocking
```

### Example 3: Research Evaluation
```
Scenario: Comparing different scanner models
Priority: Objective comparison
Recommended Metrics: F1 Score as primary, all metrics for comprehensive analysis
```

## Interpreting Results

### Good Performance Indicators
- **Accuracy**: > 85% (depending on dataset complexity)
- **F1 Score**: > 80% (good balance)
- **Precision**: > 90% (if false positives are costly)
- **Recall**: > 90% (if security is critical)

### Warning Signs
- **Accuracy < 70%**: Scanner may not be suitable for production
- **Precision < 60%**: Too many false positives
- **Recall < 60%**: Missing too many real threats
- **Large gap between Precision and Recall**: Scanner may need tuning

## Common Pitfalls

### 1. Focusing Only on Accuracy
- Accuracy can be misleading with imbalanced datasets
- A scanner that always says "safe" might have high accuracy on a dataset with mostly safe prompts

### 2. Ignoring the Business Context
- Choose metrics based on your specific use case
- Security applications need different priorities than user experience applications

### 3. Not Considering the Dataset
- Metrics depend heavily on the test dataset
- Ensure your dataset is representative of real-world usage

### 4. Over-optimizing One Metric
- Balance is key - don't sacrifice one metric completely for another
- Use F1 score to find the optimal balance point

## Performance Metrics

### Throughput
- **Definition**: Number of prompts processed per second
- **Formula**: `Total Prompts / Total Elapsed Time`
- **Units**: prompts/sec
- **Interpretation**:
  - Higher is better
  - Sequential: Baseline performance (typically 1-3 prompts/sec)
  - Concurrent: Parallel performance (can be 5-20x sequential)
- **When to Use**: Comparing processing efficiency, capacity planning

**Example**:
```
Total Prompts: 100
Total Time: 45.23 seconds
Throughput: 100 / 45.23 = 2.21 prompts/sec
```

### Request Latency
- **Definition**: Time taken for individual API calls
- **Units**: milliseconds (ms)
- **Key Statistics**:
  - **Average**: Mean latency across all requests
  - **Minimum**: Fastest request
  - **Maximum**: Slowest request
  - **p50 (Median)**: 50% of requests are faster than this
  - **p95**: 95% of requests are faster than this
  - **p99**: 99% of requests are faster than this

**Why Percentiles Matter**:
- Average can be misleading due to outliers
- p50 shows typical user experience
- p95/p99 reveal worst-case scenarios

**Example**:
```
Average: 688 ms
Minimum: 435 ms
Maximum: 2291 ms
p50: 522 ms  <- Half of requests are faster than this
p95: 1510 ms <- Only 5% of requests are slower
p99: 2135 ms <- Only 1% of requests are slower
```

### Total Elapsed Time
- **Definition**: Wall-clock time from start to finish
- **Units**: seconds
- **Note**: Sequential runs include API latency only; concurrent runs include parallelization benefits

## Comparing Sequential vs Concurrent Performance

Both evaluators now report consistent performance metrics for easy comparison:

### Sequential Evaluator Output
```
Performance Metrics:
===================

Throughput:
-----------
Overall: 1.45 prompts/sec
Total Prompts: 10
Total Elapsed Time: 6.91 seconds

Request Latency (API call time):
--------------------------------
Average: 688.06 ms
p50 (median): 522.55 ms
p95: 1509.91 ms
p99: 2134.86 ms
```

### Concurrent Evaluator Output
```
Concurrent Performance Metrics:
==============================

Configuration:
--------------
Concurrent Workers: 10

Throughput:
-----------
Overall: 6.53 prompts/sec
Total Prompts: 100
Total Elapsed Time: 15.32 seconds

Request Latency (API call time):
--------------------------------
Average: 245.12 ms
p50 (median): 221.67 ms
p95: 456.78 ms
p99: 1234.56 ms

Queue Time (waiting for worker):
--------------------------------
Average: 12.34 ms
```

### Key Differences
- **Sequential**: Shows baseline API performance without parallelization
- **Concurrent**: Adds queue time metrics and worker distribution
- **Throughput**: Concurrent should show significant improvement (5-20x)
- **Latency**: Should be similar if API is not overloaded

## Additional Resources

- Review the exported false positives and false negatives files for detailed analysis
- Use the confusion matrix to understand specific failure patterns
- Consider creating custom datasets that match your specific use case
- Regular evaluation helps track scanner performance over time
- Compare sequential vs concurrent runs to understand API scaling behavior
