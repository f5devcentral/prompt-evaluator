# PDF Report Features

## Overview

The PDF report generator creates comprehensive evaluation reports that include both accuracy metrics and performance statistics. Reports are automatically generated after each evaluation run.

## Report Sections

### 1. Title Page
- Report title with dataset name
- Generation timestamp

### 2. Executive Summary
- Overview of evaluation scope
- Key metrics at a glance:
  - Overall Accuracy
  - Precision
  - Recall
  - F1 Score

### 3. Performance Metrics
- **Detailed metrics table** showing all classification outcomes
- **Visual bar chart** of key metrics (Accuracy, Precision, Recall, F1 Score)

### 4. Confusion Matrix Analysis
- **Confusion matrix table** with color-coded cells:
  - Green: Correct predictions (TP, TN)
  - Red: Errors (FP, FN)
- **Visual confusion matrix chart** for easy interpretation
- Explanatory text about matrix interpretation

### 5. Detailed Analysis
Breakdown of each classification type:
- **True Positives**: Correctly flagged malicious prompts
- **True Negatives**: Correctly cleared safe prompts
- **False Positives**: Incorrectly flagged safe prompts
- **False Negatives**: Incorrectly cleared malicious prompts

Each section includes counts and percentage of total dataset.

### 6. Performance Statistics (NEW)

#### Throughput Section
Shows processing efficiency:
- **Overall Throughput**: Prompts processed per second
- **Total Prompts Processed**: Count of all evaluated prompts
- **Total Elapsed Time**: Wall-clock time for evaluation

**Example:**
```
Throughput
----------
Overall Throughput: 2.38 prompts/sec
Total Prompts Processed: 10
Total Elapsed Time: 4.19 seconds
```

#### Request Latency Section
Shows API response time distribution:
- **Basic Statistics**:
  - Average latency
  - Minimum latency
  - Maximum latency

- **Percentile Statistics** (NEW):
  - **p50 (median)**: 50% of requests are faster than this
  - **p95**: 95% of requests are faster than this
  - **p99**: 99% of requests are faster than this

**Example:**
```
Request Latency
---------------
Average: 417.47 ms
Minimum: 231.12 ms
Maximum: 1329.30 ms

Latency Percentiles:
p50 (median): 272.40 ms - 50% of requests are faster
p95: 1002.42 ms - 95% of requests are faster
p99: 1263.92 ms - 99% of requests are faster
```

#### Latency Distribution Chart (NEW)
Visual bar chart showing:
- Avg, Min, Max (basic metrics)
- p50, p95, p99 (percentiles)

Color-coded for easy interpretation:
- Blue: Average
- Gray: Min/Max range
- Green: p50 (typical experience)
- Orange: p95 (most users)
- Red: p99 (worst case)

#### Interpretation Guide (NEW)
Built-in explanation of percentiles:
> "Percentiles show the distribution of latency across all requests. For example, p95 indicates that 95% of requests completed faster than this time, helping identify worst-case user experiences."

### 7. Example Errors
Sample false positives and false negatives (first 5 of each):
- Shows actual prompts that were misclassified
- Helps identify patterns in scanner behavior
- Useful for debugging and improvement

### 8. Conclusion
- Summary of key findings
- Recommendations for optimization

## What's New in Enhanced Reports

### Performance Metrics Added
1. **Throughput metrics** - Understand processing capacity
2. **Latency percentiles** - See beyond averages to understand distribution
3. **Visual latency chart** - Quick visual assessment of performance
4. **Percentile interpretation** - Built-in explanations

### Benefits

#### For Performance Analysis
- **Baseline establishment**: Document sequential performance
- **Comparison ready**: Metrics match concurrent evaluator format
- **Complete picture**: Both accuracy AND performance in one report

#### For Decision Making
- **Capacity planning**: Use throughput for sizing infrastructure
- **SLA definition**: Use percentiles (p95/p99) for realistic SLAs
- **User experience**: Understand worst-case latency

#### For Debugging
- **Performance patterns**: Identify if issues are systematic or outliers
- **Correlation analysis**: Compare accuracy vs. latency
- **Historical tracking**: Archive reports for trend analysis

## Generating Reports

### Automatic Generation
Reports are automatically generated after each evaluation:
```bash
python prompt_evaluator.py -i datasets/test_dataset.jsonl
# Creates: results/test_dataset_report.pdf
```

### Manual Generation
Generate report from existing results:
```bash
python report_generator.py --dataset test_dataset
# Looks in results/ directory for test_dataset_results.*
```

### Supported Input Formats
The report generator works with results in any format:
- JSONL (recommended)
- CSV
- TSV
- Parquet

## Notes

### Throughput Availability
- **During evaluation**: Full throughput metrics (prompts/sec, total time)
- **From saved results**: Latency percentiles only (no total time saved in files)

### Percentile Calculations
- Require at least 10 data points for meaningful results
- Use numpy's percentile function (linear interpolation)
- Based on actual API response times

### Chart Quality
- Generated at 150 DPI for crisp printing
- Optimized for letter/A4 page size
- Professional color scheme

## Tips for Using Reports

1. **Compare over time**: Archive reports to track performance trends
2. **Share with stakeholders**: Professional format suitable for presentations
3. **Focus on percentiles**: Don't rely solely on averages
4. **Check p99**: This represents worst-case user experience
5. **Correlate metrics**: Look for patterns between accuracy and performance

## Example Use Cases

### Scenario 1: Performance Baseline
Run evaluation, archive PDF report with current date. Use as baseline for future comparisons.

### Scenario 2: A/B Testing
Generate reports for different scanner configurations. Compare accuracy AND performance side-by-side.

### Scenario 3: Capacity Planning
Use throughput metrics from reports to calculate required infrastructure for production load.

### Scenario 4: SLA Definition
Use p95/p99 metrics from reports to set realistic response time SLAs.

## Related Documentation

- [Evaluation Metrics Guide](evaluation-metrics.md) - Detailed metric explanations
- [Sequential vs Concurrent Comparison](SEQUENTIAL_VS_CONCURRENT.md) - Performance comparison guide
- [Usage Guide](usage.md) - General evaluation usage
