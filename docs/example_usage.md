# Misclassification export examples

FP/FN exports use the same binary policy as online evaluation and reports: flagged, blocked, and redacted are detections; cleared is no detection. Request failures, incomplete guardrail executions, and invalid rows are excluded rather than mislabeled FP/FN.

After confirming the tenant and project, these live examples select CSV for main results and exports:

```bash
python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl --lines 10 --project evaluation-project --results-format csv --format csv --output baseline.csv
python prompt_evaluator_prompts.py --input datasets/sample-datasets/pii_dataset.jsonl --max-lines 10 --project evaluation-project --provider evaluation-provider --format csv --output pipeline.csv
```

Main results are `results/baseline.csv` or `results/pipeline.csv`. FP/FN exports remain dataset-derived: `results/pii_dataset_false_positives.csv` and `results/pii_dataset_false_negatives.csv`. They are standard comma-separated CSV, not pipe-delimited. All exports include available source provenance and safe scanner evidence; nested structures are JSON cells.

Without explicit format flags, scan main results use JSONL, prompts main results use CSV, and FP/FN exports use JSONL in both modes. Concurrent outputs include `_concurrent` in their default names. Archive prior runs before intentionally reusing names.

Reports recompute examples from main results instead of trusting these sidecars. Result files and PDF examples can contain PII; review content and access before sharing. See [usage](usage.md), [formats](results-format-changes.md), and [metrics](evaluation-metrics.md).
