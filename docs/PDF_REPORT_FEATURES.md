# PDF report features

Reports show evaluation scope, attempted/evaluated coverage, request errors, incomplete guardrail results, invalid rows, and provider failures separately. Detection metrics use evaluated rows only and agree with online scoring and offline reanalysis.

The confusion-matrix table and chart both use actual-class rows and predicted-class columns: `[[TP, FN], [FP, TN]]`. Binary detections include `flagged`, `blocked`, and `redacted`; raw outcomes remain in source results. FP/FN examples are recomputed from those results rather than potentially stale sidecar exports.

Accuracy, precision, recall, F1, latency means/ranges, p50/p95/p99, and latency charts are available. Evaluable-row latency excludes operational failures. Live sequential/prompt evaluation can supply wall time for attempt throughput; standalone reports don't infer it from per-request durations. Small samples make percentiles unstable.

Sequential scans and prompts generate PDFs automatically. Concurrent scans require `python report_generator.py --dataset dataset_concurrent` or `--input` with the exact result path. Parquet is supported when its optional engine is installed.

Scope warnings distinguish aggregate `/prompts` pipeline outcomes from scanner-specific accuracy. Zero-evaluation reports don't provide an accuracy estimate. Comparative reports with a zero-evaluation configuration display coverage only.

Examples can contain original prompt text and PII. Default results and PDFs aren't automatically sanitized for sharing. See [report usage](pdf-reports.md), [metrics](evaluation-metrics.md), and [result compatibility](results-format-changes.md).
