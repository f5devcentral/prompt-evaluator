# PDF Report Generation

## Overview

The PDF Report Generator creates professional, visually appealing reports from your evaluation results. These reports include comprehensive metrics, visualizations, and detailed analysis of AI safety scanner performance.

## Features

- **Professional Design**: Modern, clean layout with color-coded sections
- **Comprehensive Metrics**: All key performance indicators including accuracy, precision, recall, and F1 score
- **Visual Charts**: 
  - Confusion matrix heatmap
  - Bar charts for key metrics
- **Detailed Analysis**: Breakdown of true/false positives and negatives
- **Example Errors**: Sample false positives and false negatives
- **Performance Statistics**: Latency and response time metrics

## Installation

Install the required dependencies:

```bash
pip install reportlab matplotlib numpy
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Automatic Generation

PDF reports are now **automatically generated** after each evaluation completes!

```bash
# Run evaluation - PDF report is generated automatically
python prompt_evaluator.py --input datasets/pii_dataset.csv

# Or with the prompts API
python prompt_evaluator_prompts.py --input datasets/pii_dataset.csv
```

The PDF report will be saved alongside your results in the `results/` directory.

### Manual Generation (Optional)

You can also generate reports manually for existing results:

```bash
python report_generator.py --dataset pii_dataset
```

### Specify Results Directory

If your results are in a different directory:

```bash
python report_generator.py --dataset pii_dataset --results-dir /path/to/results
```

### Custom Output Path

Specify a custom output path for the PDF:

```bash
python report_generator.py --dataset pii_dataset --output my_report.pdf
```

### Auto-detect Dataset

If you only have one dataset in your results folder, you can omit the dataset name:

```bash
python report_generator.py
```

## Report Contents

The generated PDF report includes the following sections:

### 1. Title Page
- Dataset name
- Generation timestamp
- Professional formatting

### 2. Executive Summary
- Overview of evaluation
- Key metrics at a glance
- Total samples analyzed

### 3. Performance Metrics
- Accuracy
- Precision
- Recall
- F1 Score
- Confusion matrix breakdown
- Visual bar chart

### 4. Confusion Matrix Analysis
- Visual confusion matrix heatmap
- Color-coded results (green = correct, red = errors)
- Detailed table breakdown

### 5. Detailed Analysis
- True Positives (correctly flagged)
- True Negatives (correctly cleared)
- False Positives (incorrectly flagged)
- False Negatives (incorrectly cleared)

### 6. Performance Statistics
- Average response time
- Minimum response time
- Maximum response time

### 7. Example Errors
- Sample false positive prompts
- Sample false negative prompts
- Helps identify patterns in errors

### 8. Conclusion
- Summary of findings
- Recommendations
- Next steps

## Report Structure

```
┌─────────────────────────────┐
│   Title Page                │
├─────────────────────────────┤
│   Executive Summary         │
├─────────────────────────────┤
│   Performance Metrics       │
│   └─ Metrics Table          │
│   └─ Metrics Chart          │
├─────────────────────────────┤
│   Confusion Matrix          │
│   └─ Confusion Matrix Table │
│   └─ Confusion Matrix Chart │
├─────────────────────────────┤
│   Detailed Analysis         │
│   ├─ True Positives         │
│   ├─ True Negatives         │
│   ├─ False Positives        │
│   └─ False Negatives        │
├─────────────────────────────┤
│   Performance Statistics    │
│   └─ Latency Metrics        │
├─────────────────────────────┤
│   Example Errors            │
│   ├─ False Positives        │
│   └─ False Negatives        │
├─────────────────────────────┤
│   Conclusion                │
└─────────────────────────────┘
```

## Requirements

The PDF generator expects results files in the following format:

### Results Directory Structure

```
results/
├── {dataset_name}_results.csv
├── {dataset_name}_false_positives.jsonl
└── {dataset_name}_false_negatives.jsonl
```

### Results CSV Format

The CSV file should contain columns:
- `prompt`: The prompt text
- `expected`: Expected outcome (true/false)
- `outcome`: Scanner outcome (flagged/cleared)
- `response_time`: API response time in seconds

### False Positives/Negatives Format

JSONL files with JSON objects containing:
```json
{
  "prompt": "Sample prompt text",
  "expected": "false",
  "outcome": "flagged",
  "response_time": 0.123,
  "prompt_size": 45,
  "original_line": "...",
  "metadata": {...}
}
```

## Command Line Options

```bash
python report_generator.py [OPTIONS]

Options:
  -d, --dataset TEXT      Dataset name (e.g., pii_dataset)
  -r, --results-dir TEXT  Results directory (default: results)
  -o, --output TEXT       Output PDF path
  -h, --help             Show help message
```

## Examples

### Example 1: Basic Report Generation

```bash
# Generate report for PII dataset
python report_generator.py --dataset pii_dataset

# Output: results/pii_dataset_report.pdf
```

### Example 2: Custom Output Location

```bash
# Generate report with custom output path
python report_generator.py --dataset fin_advice_dataset --output /tmp/financial_report.pdf

# Output: /tmp/financial_report.pdf
```

### Example 3: Multiple Datasets

```bash
# If you have multiple datasets, specify which one
python report_generator.py --dataset eu-ai-act-prompts

# Output: results/eu-ai-act-prompts_report.pdf
```

### Example 4: Automatic Workflow

With automatic PDF generation enabled:

```bash
# Run evaluation - PDF is generated automatically
python prompt_evaluator.py --input datasets/pii_dataset.csv

# The PDF report is saved as: results/pii_dataset_report.pdf
```

## Report Customization

The PDF generator creates professionally styled reports with:

- **Color Scheme**:
  - Primary: Blue (#3498DB)
  - Success: Green (#2ECC71)
  - Error: Red (#E74C3C)
  - Warning: Orange (#F39C12)
  - Text: Dark gray (#2C3E50)

- **Typography**:
  - Headers: Helvetica-Bold
  - Body: Helvetica
  - Professional sizing and spacing

- **Visual Elements**:
  - Color-coded tables
  - Gradient confusion matrices
  - Bar charts with value labels
  - Consistent formatting throughout

## Troubleshooting

### Missing Dependencies

If you see an import error:

```bash
pip install reportlab matplotlib numpy
```

### No Results Found

If the generator can't find results:

1. Check that results files exist in the expected location
2. Verify the dataset name matches the file names
3. Ensure the results directory path is correct

### Chart Generation Issues

If charts don't appear:
- Ensure matplotlib backend is properly installed
- Check that numpy is installed and working
- Verify sufficient disk space for temporary files

## Integration with Evaluation Flow

You can integrate PDF generation into your workflow:

```python
from report_generator import PDFReportGenerator, load_evaluation_results

# Load results
results = load_evaluation_results('my_dataset')

# Generate report
generator = PDFReportGenerator()
output_path = generator.generate_report(
    dataset_name='my_dataset',
    metrics=results['metrics'],
    false_positives=results['false_positives'],
    false_negatives=results['false_negatives'],
    latency_stats=results['latency_stats']
)

print(f"Report saved to: {output_path}")
```

## Best Practices

1. **Automatic Generation**: PDF reports are generated automatically after each evaluation
2. **Share Reports**: PDF reports are easy to share with stakeholders
3. **Archive Reports**: Keep historical reports for comparison over time
4. **Review Metrics**: Use the detailed breakdown to identify improvement areas
5. **Install Dependencies**: If PDF dependencies aren't installed, you'll see a warning but evaluation will continue

## Output

The generated PDF report provides:

- ✅ Professional, presentation-ready format
- ✅ Complete performance analysis
- ✅ Visual representations of data
- ✅ Actionable insights
- ✅ Easy sharing and archiving

This makes it perfect for:
- Presenting results to management
- Documentation and records
- Sharing with stakeholders
- Performance tracking over time
- Compliance and audit purposes
