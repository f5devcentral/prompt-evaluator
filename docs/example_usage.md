# False Positives and False Negatives Export Feature

This document demonstrates the new export feature that creates separate CSV files for False Positives and False Negatives to help with troubleshooting.

## What's New

The evaluator now automatically exports two additional CSV files:
- `{output_file}_false_positives.csv` - Contains prompts that were incorrectly flagged as malicious
- `{output_file}_false_negatives.csv` - Contains prompts that were incorrectly cleared when they should have been flagged

## Usage Examples

### Basic Usage (prompt_evaluator.py)
```bash
python prompt_evaluator.py --input dataset.csv --output results.csv
```

This will create:
- `results.csv` - Main results file
- `results_false_positives.csv` - False positives for troubleshooting
- `results_false_negatives.csv` - False negatives for troubleshooting

### Advanced Usage (prompt_evaluator_prompts.py)
```bash
python prompt_evaluator_prompts.py --input dataset.csv --output prompts_results.csv
```

This will create:
- `prompts_results.csv` - Main results file with LLM responses
- `prompts_results_false_positives.csv` - False positives with detailed scanner results
- `prompts_results_false_negatives.csv` - False negatives with detailed scanner results

## File Format

### False Positives CSV Format
```
prompt|expected|outcome|response_time|prompt_size|original_line
```

### False Negatives CSV Format (prompt_evaluator_prompts.py)
```
prompt|expected|outcome|response|response_time|prompt_size|scanner_results|original_line
```

## Benefits

1. **Focused Analysis**: Quickly identify problematic prompts without filtering through all results
2. **Troubleshooting**: Understand why certain prompts were misclassified
3. **Model Improvement**: Use these files to improve training data or adjust thresholds
4. **Quality Assurance**: Review edge cases that need attention

## Example Output

When you run an evaluation, you'll see output like:
```
Exported 15 false positives to results_false_positives.csv
Exported 8 false negatives to results_false_negatives.csv
```

This helps you understand the distribution of errors in your evaluation results.
