# PDF reports

Reports use the same detection policy, exclusions, and denominator as live evaluation. Metrics and FP/FN examples are recomputed from the selected main result file, not stale export sidecars. The chart's rows are actual malicious/safe classes and columns are predicted detection/no detection: `[[TP, FN], [FP, TN]]`.

## Generate a report

Sequential scans and prompts generate PDFs automatically when dependencies are available. Concurrent scans don't. Manual reporting is offline:

```bash
conda activate prompt-evaluator
python report_generator.py --dataset pii_dataset
python report_generator.py --dataset pii_dataset_concurrent
python report_generator.py --input results/custom.jsonl --output results/custom_report.pdf
python report_generator.py --dataset pii_dataset --results-dir /path/to/archived/results
```

`--dataset` is a name without `_results`, extension, or path. Lookup precedence remains JSONL, CSV, TSV, then Parquet. If multiple formats exist for the same dataset, use `--input` to select the exact file. Custom main filenames also use `--input`.

## Read the report

The executive summary and metrics table identify attempted and evaluated samples plus request errors, incomplete guardrail results, invalid rows, and separate provider failures. `flagged`, `blocked`, and `redacted` count as detections. With no evaluable rows, zero rates are placeholders rather than accuracy estimates.

Scope is explicit: `/prompts` summarizes a provider pipeline and can include response guardrails; it isn't isolated input-scanner accuracy. Historical/mixed scope is labeled when unavailable. Legacy opaque scanner fields cannot establish execution completeness.

Reports include confusion-matrix charts/tables, accuracy/precision/recall/F1, misclassification examples, and available request-latency statistics. Latency uses evaluable rows, never zero-duration error placeholders. Live sequential runs supply wall time for attempt throughput; standalone loading doesn't reconstruct it from request durations.

The specialized `comparative_report_generator.py` retains its configured dataset comparison layout but shares metric calculation and derives examples from source rows. Its per-configuration tables disclose exclusions. If any configuration has no evaluated rows, it produces a coverage-only report rather than comparative accuracy conclusions.

## Dependencies and sensitive data

Activate Conda and install `requirements.txt`; ReportLab, Matplotlib, and NumPy are included. Parquet additionally needs `requirements-parquet.txt`. No API token is needed for reports or imports/help.

PDF examples may contain original prompts and PII. Review the selected results, access controls, and retention before sharing. Report errors don't imply the underlying evaluation result file was lost; regenerate from that file after addressing the local dependency or output-path problem.

See [metrics](evaluation-metrics.md), [formats](results-format-changes.md), and [report features](PDF_REPORT_FEATURES.md).
