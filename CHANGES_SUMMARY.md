# What's new in prompt-evaluator

This update brings prompt-evaluator's scan and prompt evaluation workflows in line with the latest CalypsoAI API. It focuses on clearer results, more control over evaluation runs, and consistent reporting.

## Understand what your guardrails detected

Results now account for all current guardrail outcomes, including blocked and redacted content. Flagged, blocked, and redacted prompts count as detections; cleared prompts count as no detection. The original outcome is still saved so you can see what happened.

Failed requests, incomplete scans, and invalid records are shown separately instead of disappearing from the totals or being mistaken for successful evaluations. You can see how many prompts were attempted and how many could actually be scored.

## Choose the configuration you want to evaluate

Select a project with `--project` rather than relying only on global settings. When evaluating LLM responses, use `--provider` to choose the configured provider you want to test. Existing defaults still apply when you leave these options out.

You can also set a request timeout and request additional scanner details when troubleshooting. US1, EU1, and custom tenant addresses are supported.

## Get consistent exports and reports

Console results, saved-result analysis, false-positive/false-negative exports, and PDF reports now use the same scoring rules. PDF charts correctly distinguish false positives from false negatives, and report examples are rebuilt from the selected results rather than potentially outdated export files.

Choose JSONL, CSV, TSV, or optional Parquet output, including for the LLM-response evaluator. Custom output names are now honored. Scan tools keep their JSONL default, while the LLM-response evaluator keeps its CSV default.

## Run evaluations more predictably

Requests have configurable timeouts, and concurrent runs measure the time prompts actually spend waiting for a worker. Missing, unreadable, or empty inputs and conflicting output filenames are caught before prompts are sent or result files are written. Ordinary output names can still be reused intentionally, so archive runs you need to keep.

Setup validation now runs locally without contacting the API unless you explicitly request a connection check. Credentials and generated results stay excluded from Git; only an empty placeholder preserves the results directory.

## Keep using your existing data

Existing datasets and supported result files remain usable without a required migration or another API run. Recalculated scores may change because blocked/redacted outcomes and failed evaluations are now handled consistently. Older files that lack detailed scanner information can't provide that missing history.

Parquet needs the optional dependencies described in the [installation guide](docs/installation.md). Command examples and output defaults are covered in the [usage guide](docs/usage.md), and the [metrics guide](docs/evaluation-metrics.md) explains how to interpret the results.

Results and PDF examples can contain prompts, personal information, and LLM responses. Review them before sharing, and enable extra diagnostic content only when you need it.
